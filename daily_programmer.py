import praw
import re
import datetime as dt
import os

import reddit_api as api

MIN_TIMESTAMP = 86400


def parse_date(date):
    """Returns input dates to required formats. Edge cases without recognized formats are returned differently."""
    frmts = ('%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%d/%m/%Y', '%d/%#m/%y')
    for f in frmts:
        try:
            d = dt.datetime.strptime(date, f)
            return d.strftime('%Y%m%d')
        except ValueError:
            pass
    else:
        return date.replace('/', '_').replace('-', '_')


def create_title(title, n=[0]):
    """
    Takes the original title of the post and formats it according to a consistent standard.
    Most posts should return 'DP' followed by date followed by a letter indicating type of post. Date format is
    dictated by parse_date function. Post types: A: easy, B: intermediate, C: hard, W: weekly, M: monthly
    """
    results = []
    catcher = False
    new_title = ''
    title = re.sub('((?<=\[\d{4})-(?=\d-\d{2}]))', '-0', title)
    search = re.search('((?<=\[)[0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}(?=]))|((?<=\[)[0-9]{4}-[0-9]{2}-[0-9]{2}(?=]))',
                       title)
    if search:
        new_date = parse_date(search.group())
        new_title += new_date
        n[0] = int(new_date)
        catcher = True
    else:
        new_title += str(n[0]).zfill(8)
        n[0] += 1

    lower_title = title.lower()
    if '[easy]' in lower_title:
        new_title += 'A'
        catcher = True
    if 'intermediate]' in lower_title \
            or 'intemerdiate]' in lower_title \
            or 'med]' in lower_title:
        new_title += 'B'
        catcher = True
    if '[difficult]' in lower_title \
            or 'hard]' in lower_title:
        new_title += 'C'
        catcher = True
    if 'weekly #' in lower_title \
            or '[weekly]' in lower_title \
            or re.search('((?<!: )week-long)', lower_title):
        new_title += 'W'
        catcher = True
    if 'monthly challenge' in lower_title:
        new_title += 'M'
        catcher = True

    if catcher:
        if new_title in results:
            new_title += '_'
        return new_title
    else:
        return None


def content_wrap(text):
    """Wraps the content of the post to wrap like a word processor would."""
    length = 120
    result = []
    for i in text.split('\n'):
        while i:
            if len(i) > length:
                loc = i.rfind(' ', 0, length)
                if loc == -1:
                    loc = i.find(' ', length)
                result.append(i[:loc])
                if loc == -1:
                    i = ""
                else:
                    i = i[loc + 1:]

            else:
                result.append(i)
                i = ""
    return result


def create_file(p, start_time=0):
    """Creates .py file with original title, URL and post contents inside, with a ready to go main function in place."""
    title = p.title
    filename = create_title(title)
    if not filename:
        return
    if p.created - start_time <= 0:
        return True
    filename = 'DP' + filename + '.py'

    url = p.url
    content = p.selftext
    print(filename)

    with open(filename, 'a', encoding='UTF-8') as f:
        f.write('"""\n')
        f.write(title + '\n\n')
        f.write(url + '\n\n')
        for line in content_wrap(content):
            f.write(line + '\n')
        f.write('"""\n')
        f.write('\n\n')
        f.write('def main():\n')
        f.write('    pass\n')
        f.write('\n\n')
        f.write('if __name__ == "__main__":\n')
        f.write('    main()\n')


def get_latest_file_time(reddit):
    """Returns the timestamp of the the newest previously created file."""
    file_list = sorted(os.listdir('.'), reverse=True)
    for file in file_list:
        if file.startswith('DP') and file.endswith('.py') and '_' not in file:
            break
    else:
        return MIN_TIMESTAMP

    with open(file, 'r') as f:
        for r in range(3):
            f.readline()
        url = f.readline().strip()
    submission = reddit.submission(url=url)
    return submission.created


def main():
    reddit = praw.Reddit(client_id=api.client_id,
                         client_secret=api.client_secret,
                         user_agent=api.user_agent)

    start_time = get_latest_file_time(reddit)
    print("Time threshold: {}".format(dt.datetime.fromtimestamp(start_time)))

    posts = []
    for submission in reddit.subreddit('dailyprogrammer').submissions():
        posts.append(submission)

    if start_time == MIN_TIMESTAMP:
        posts.reverse()
    for p in posts:
        stop = create_file(p, start_time)
        if stop:
            break


if __name__ == "__main__":
    main()
