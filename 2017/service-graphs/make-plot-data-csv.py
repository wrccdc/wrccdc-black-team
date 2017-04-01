import os
import re
import csv
import datetime
import pytz
import bokeh
import numpy as np

from bokeh.io import output_file, show, save, reset_output
from bokeh.layouts import row, gridplot
from bokeh.models import DatetimeTickFormatter, Range1d, PanTool, WheelZoomTool, BoxZoomTool, ZoomInTool, ZoomOutTool, UndoTool, HoverTool, ResetTool, SaveTool
#from bokeh.plotting import figure, output_file, show, save
from bokeh.plotting import figure #, save
from bokeh.models.sources import ColumnDataSource

services = [
	'archer-http',
	'archer-https',
	'bob-http',
	'bob-https',
	'cyril-ftp',
	'cyril-http',
	'cyril-https',
	'cyril-ssh2',
	'ethan-http',
	'ethan-pop3',
	'ethan-smtp',
	'frylock-http',
	'frylock-https',
	'frylock-ssh2',
	'lana-http',
	'lana-https',
	'lana-pop3',
	'lana-smtp',
	'lana-ssh2',
	'linda-http',
	'linda-https',
	'louise-http',
	'louise-https',
	'malory-dns',
	'meatwad-ssh2',
	'morty-dns',
	'morty-f4d-dns',
	'morty-spy-dns',
	'nancy-http',
	'nancy-https',
	'orangevm-custom',
	'pam-dns',
	'shake-http',
	'shake-https',
	'shake-ssh2',
]

by_team = {
    'Team 01': {},
    'Team 02': {},
    'Team 03': {},
    'Team 04': {},
    'Team 05': {},
    'Team 06': {},
    'Team 07': {},
    'Team 08': {},
}


sla_violations = {}

cwd = os.getcwd()

with open('{}/sla-violations.csv'.format(cwd)) as csvfile:
    reader = csv.DictReader(csvfile)
    
    for row in reader:
        sla_violations[row['laststatusID']] = int(row['points'])
        

for service in services:
    for team in by_team:
        by_team[team][service] = {'check_num': [], 'datetime': [], 'points': [], 'total_points': [], 'sla_violations': {'datetime': [], 'points': [], 'check_num': []}}

with open('{}/service-checks-time-adjusted.csv'.format(cwd)) as csvfile:
    reader = csv.DictReader(csvfile)
    
    for row in reader:
        by_team[row['teamname']][row['servicename']]['check_num'].append(int(row['checknumber']))
        by_team[row['teamname']][row['servicename']]['datetime'].append(row['starttime'])
        by_team[row['teamname']][row['servicename']]['points'].append(int(row['points']))

        if by_team[row['teamname']][row['servicename']]['total_points']:
            by_team[row['teamname']][row['servicename']]['total_points'].append(by_team[row['teamname']][row['servicename']]['total_points'][-1] + int(row['points']))
        else:
            by_team[row['teamname']][row['servicename']]['total_points'].append(int(row['points']))

        if row['id'] in sla_violations:
            by_team[row['teamname']][row['servicename']]['total_points'][-1] += sla_violations[row['id']]
            by_team[row['teamname']][row['servicename']]['sla_violations']['points'].append(by_team[row['teamname']][row['servicename']]['total_points'][-1])
            by_team[row['teamname']][row['servicename']]['sla_violations']['datetime'].append(row['starttime'])
            by_team[row['teamname']][row['servicename']]['sla_violations']['check_num'].append(row['checknumber'])

#import pprint
#pprint.pprint(by_team)

# offset by 7 because bokeh is brokeh
x_start = (datetime.datetime(2017,3,24,8,30,0) - datetime.timedelta(hours=7)).timestamp() * 1000
x_end = (datetime.datetime(2017,3,25,21,0,0) - datetime.timedelta(hours=7)).timestamp() * 1000

colors = bokeh.palettes.viridis(len(services))
color_index = 0

#print(colors)

#TOOLS = 'pan,wheel_zoom,box_zoom,zoom_in,zoom_out,undo,hover,reset,save'


GRAPH_WIDTH = 1600
GRAPH_HEIGHT = 950

ONE_ONLY = False

import copy

for team in sorted(by_team):
    if ONE_ONLY and '01' not in team:
        continue
    #print('hit')

    output_file(re.sub('[^a-z0-9./-]', '', "html/{}-service-graphs.html".format(team).lower()))

    plot_list = []

    hover = HoverTool(tooltips=[('Service', '@service_name'), ('Check Number', '@check_num'), ('Total Points', '@total_points'), ('Check Time', '@str_datetimes')])

    TOOLS = [PanTool(), WheelZoomTool(), BoxZoomTool(), ZoomInTool(), ZoomOutTool(), UndoTool(), hover, ResetTool(), SaveTool()]

    all_services_plot = figure(title="{} - {}".format(team, service), x_axis_label='Time', y_axis_label='{} Service Points'.format(service), x_axis_type="datetime", x_range=Range1d(x_start, x_end), width=GRAPH_WIDTH, height=GRAPH_HEIGHT, tools=TOOLS)


    for service in by_team[team]:

        column_data = ColumnDataSource({
            'service_name': [service for x in by_team[team][service]['check_num']],
            'check_num': by_team[team][service]['check_num'],
            'datetimes': np.array(by_team[team][service]['datetime'], dtype=np.datetime64),
            'str_datetimes': by_team[team][service]['datetime'],
            'total_points': by_team[team][service]['total_points'],
        })

        sla_column_data = ColumnDataSource({
            'service_name': ['{} (SLA)'.format(service) for x in by_team[team][service]['sla_violations']['datetime']],
            'datetimes': np.array(by_team[team][service]['sla_violations']['datetime'], dtype=np.datetime64),
            'str_datetimes': by_team[team][service]['sla_violations']['datetime'],
            'total_points': by_team[team][service]['sla_violations']['points'],
            'check_num': by_team[team][service]['sla_violations']['check_num'],
        })

        hover = HoverTool(tooltips=[('Service', '@service_name'), ('Check Number', '@check_num'), ('Total Points', '@total_points'), ('Check Time', '@str_datetimes')])

        TOOLS = [PanTool(), WheelZoomTool(), BoxZoomTool(), ZoomInTool(), ZoomOutTool(), UndoTool(), hover, ResetTool(), SaveTool()]
        #output_file(re.sub('[^a-z0-9./-]', '', "html/{}-{}.html".format(team, service).lower()))
        p = figure(title="{} - {}".format(team, service), x_axis_label='Time', y_axis_label='{} Service Points'.format(service), x_axis_type="datetime", x_range=Range1d(x_start, x_end), width=GRAPH_WIDTH, height=GRAPH_HEIGHT, tools=TOOLS)
        p.xaxis.formatter=DatetimeTickFormatter(hours=["%X"], days=["%m/%d"], months=["%m"], years=["%Y"])
        #datetimes = np.array(by_team[team][service]['datetime'], dtype=np.datetime64)
        #sla_datetimes = np.array(by_team[team][service]['sla_violations']['datetime'], dtype=np.datetime64)
        #p.line(x=datetimes, y=np.array(by_team[team][service]['points']), legend='Service Scores', line_width=2)

        p.circle(x='datetimes', y='total_points', legend='Total Points', line_width=2, line_color=colors[color_index], source=column_data)
        all_services_plot.circle(x='datetimes', y='total_points', legend=service, line_width=2, line_color=colors[color_index], source=column_data)
        
        p.circle(x='datetimes',y='total_points', legend='SLA Violations', fill_color='red', size=10, source=sla_column_data)
        all_services_plot.circle(x='datetimes',y='total_points', legend='SLA Violations', fill_color='red', size=10, source=sla_column_data)


        # show the results
        #save(p)
        plot_list.append(p)
        
        #save(row(p))

        color_index += 1

        if color_index >= len(colors):
            color_index = 0

    #print(plot_list)
    plot_list.append(all_services_plot)
    print(len(plot_list))
    show(gridplot(plot_list, ncols=1))
    reset_output()


exit()




#############################################




for team in by_team:
    if ONE_ONLY and '01' not in team:
        continue
    hover = HoverTool(tooltips=[('Service', '@service_name'), ('Check Number', '@check_num'), ('Total Points', '@total_points'), ('Check Time', '@str_datetimes')])

    TOOLS = [PanTool(), WheelZoomTool(), BoxZoomTool(), ZoomInTool(), ZoomOutTool(), UndoTool(), hover, ResetTool(), SaveTool()]
    output_file(re.sub('[^a-z0-9./-]', '', "html/{}-all-services.html".format(team).lower()))
    #print('hit')
    p = figure(title="{} - All Services".format(team), x_axis_label='Time', y_axis_label='Service Points', x_axis_type="datetime", x_range=Range1d(x_start, x_end), width=GRAPH_WIDTH, height=GRAPH_HEIGHT, tools=TOOLS)
    p.xaxis.formatter=DatetimeTickFormatter(hours=["%X"], days=["%m/%d"], months=["%m"], years=["%Y"])

    for service in by_team[team]:

        column_data = ColumnDataSource({
            'service_name': [service for x in by_team[team][service]['check_num']],
            'check_num': by_team[team][service]['check_num'],
            'datetimes': np.array(by_team[team][service]['datetime'], dtype=np.datetime64),
            'str_datetimes': by_team[team][service]['datetime'],
            'total_points': by_team[team][service]['total_points'],
        })

        sla_column_data = ColumnDataSource({
            'service_name': ['{} (SLA)'.format(service) for x in by_team[team][service]['sla_violations']['datetime']],
            'datetimes': np.array(by_team[team][service]['sla_violations']['datetime'], dtype=np.datetime64),
            'str_datetimes': by_team[team][service]['sla_violations']['datetime'],
            'total_points': by_team[team][service]['sla_violations']['points'],
            'check_num': by_team[team][service]['sla_violations']['check_num'],
        })



        datetimes = np.array(by_team[team][service]['datetime'], dtype=np.datetime64)
        sla_datetimes = np.array(by_team[team][service]['sla_violations']['datetime'], dtype=np.datetime64)
        #p.line(x=datetimes, y=np.array(by_team[team][service]['points']), legend='Service Scores', line_width=2)
        p.circle(x='datetimes', y='total_points', legend=service, line_width=2, line_color=colors[color_index], source=column_data)
        p.circle(x='datetimes',y='total_points', legend='SLA Violations', fill_color='red', size=10, source=sla_column_data)
        color_index += 1

        if color_index >= len(colors):
            color_index = 0


        # show the results
    save(p)

    



###############
exit()

data = {}

with open('/tmp/tmp.W0VTkVlv65/service-checks-time-adjusted.csv') as csvfile:

    reader = csv.DictReader(csvfile)

    x_data = []
    y_data = []

    service_score_total = 0

    for row in reader:

        if row['servicename'] == 'archer-http' and row['owner'] == 'Team 06':
            service_score_total += int(row['points'])
#2017-03-24T18:57:46-07:00
            #x_data.append(pytz.timezone('America/Los_Angeles').localize(datetime.datetime.strptime(row['starttime'], '%Y-%m-%dT%H:%M:%S%z')))
            #y_data.append(service_score_total)
            starttime = datetime.datetime.strptime(row['starttime'], '%Y-%m-%dT%H:%M:%S')
            if starttime < datetime.datetime(2017, 3, 25):
                print('hit')
                #x_data.append(starttime)
                x_data.append(row['starttime'])
                y_data.append(service_score_total)


data['datetime'] = np.array(x_data, dtype=np.datetime64)
data['points'] = np.array(y_data)
#print(x_data)
#print(y_data)
        





# output to static HTML file
output_file("line.html")

# create a new plot with a title and axis labels
start = (datetime.datetime(2017,3,24,8,0,0) - datetime.timedelta(hours=7)).timestamp() * 1000
end = (datetime.datetime(2017,3,24,22,0,0) - datetime.timedelta(hours=7)).timestamp() * 1000
p = figure(title="simple line example", x_axis_label='x', y_axis_label='y', x_axis_type="datetime", x_range=Range1d(start, end))

# add a line renderer with legend and line thickness
p.line(data['datetime'], data['points'], legend="Temp.", line_width=2)
p.xaxis.formatter=DatetimeTickFormatter(formats=dict(
        hours=["%X"],
        days=["%m/%d"],
        months=["%m"],
        years=["%Y"],
        ))

# show the results
show(p)




exit()


"""
date_adjusted_entries = []

delta = datetime.timedelta(minutes=-52)

with open('/home/disturbedmime/logs_2017-03-25_19:59:38.sql') as sql:
    for line in sql:
        
        if not line.startswith('INSERT INTO `slaviolations` VALUES '):
            continue

        records = re.split(r'\((.*?)\),?', line[len('INSERT INTO `slaviolations` VALUES '):])

        if records:
            #count = 0
            for record in records:
                if record and len(record) > 2:
                    print(record)
                    #count += 1

                #if count > 10:
                #    exit()
"""





"""
with open('/tmp/tmp.W0VTkVlv65/service-checks.csv') as csvfile:

    reader = csv.DictReader(csvfile, quotechar="'")

    for row in reader:
        s_dt = pytz.timezone('America/Los_Angeles').localize(datetime.datetime.strptime(row['starttime'], '%Y-%m-%d %X')) 
        a_s_dt = s_dt + delta
        row['starttime'] = a_s_dt.isoformat()
        e_dt = pytz.timezone('America/Los_Angeles').localize(datetime.datetime.strptime(row['endtime'], '%Y-%m-%d %X')) 
        a_e_dt = e_dt + delta
        row['endtime'] = a_e_dt.isoformat()
        #print(row)
        date_adjusted_entries.append(row)


with open('/tmp/tmp.W0VTkVlv65/service-checks-time-adjusted.csv', 'w') as csvfile:
    field_names = ['id', 'checknumber', 'starttime', 'endtime', 'teamname', 'servicename', 'owner', 'hostname', 'status', 'points']
    writer = csv.DictWriter(csvfile, fieldnames=field_names)

    writer.writeheader()
    for row in date_adjusted_entries:
        writer.writerow(row)
"""






"""
    for line in sql:
        
        if not line.startswith('INSERT INTO `servicestatus` VALUES '):
            continue

        records = re.split(r'\((.*?)\),?', line[len('INSERT INTO `servicestatus` VALUES '):])

        if records:

            #count = 0
            for record in records:
                if record and len(record) > 2:
                    print(record)
                    #count += 1

                #if count > 10:
                #    exit()
"""
