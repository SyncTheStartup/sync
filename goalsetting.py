from calculations import calculate_average_score

def sorting_days(events):
    days = {}
    for event in events:
        day = event.get('start', {}).get('dateTime')
        print(day)
        day.split("T")
        days.setdefault(day, [])
        days[day].append(event)
    
    daily_averages = {}
    for day in days:
        daily_averages[day] = calculate_average_score(days[day])

    sorted_dict = dict(sorted(daily_averages.items(), key=lambda item: item[1]))

    print(sorted_dict)
