from datetime import datetime, timedelta, timezone
import time
import requests
from flask import Flask, jsonify, render_template
import matplotlib.pyplot as plt

app = Flask(__name__)

@app.route('/repositories/<owner>/<repo>/pulls/avg')
def avg_time_between_pulls(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = {
    }
    response = requests.get(url, headers=headers)
    pull_requests = response.json()
    time_diffs = []
    for i in range(1, len(pull_requests)):
        current = pull_requests[i]['created_at']
        current_timestamp = time.mktime(datetime.strptime(current, "%Y-%m-%dT%H:%M:%SZ").timetuple())

        previous = pull_requests[i-1]['created_at']
        previous_timestamp = time.mktime(datetime.strptime(previous, "%Y-%m-%dT%H:%M:%SZ").timetuple())
        diff = (current_timestamp - previous_timestamp)
        time_diffs.append(diff)
    avg_time_between_pulls = abs(sum(time_diffs) / len(time_diffs))
    return jsonify({"average_time_between_pulls": avg_time_between_pulls})

@app.route('/events/total/<offset>')
def total_events(offset, json=True):
    url = "https://api.github.com/events"
    headers = {
    }
    response = requests.get(url, headers=headers)
    events = response.json()
    filtered_events = []
    cutoff_time = (datetime.utcnow() - timedelta(minutes=int(offset)))
    cutoff_time = cutoff_time.replace(tzinfo=timezone.utc).replace(microsecond=0)
    for event in events:
        if event['type'] in ['WatchEvent', 'PullRequestEvent', 'IssuesEvent']:
            filtered_events.append(event)
    total_events = {}
    for event in filtered_events:
        event_type = event['type']
        created_at = datetime.fromisoformat(event['created_at'].replace('Z', '+00:00'))
        if created_at > cutoff_time:
            if event_type in total_events:
                total_events[event_type] += 1
            else:
                total_events[event_type] = 1
    if(json):
        return jsonify(total_events)   
    else:
        return total_events


#Visualization

@app.route('/events/chart/<int:offset>')
def show_total_events_chart(offset):
    event_counts = total_events(offset,False)
    if not event_counts:
        return jsonify({'error': 'No events found'})
    labels = event_counts.keys()
    counts = event_counts.values()
    fig, ax = plt.subplots()
    ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    ax.set_title(f'Total events grouped by type in the last {offset} minutes')
    plt.savefig('static/plot.png')
    return render_template('chart.html', url='/static/plot.png')

if __name__ == '__main__':
    app.run(debug=True)

