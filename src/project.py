
# TODO Repository search for Jenkinsfile + other keywords


def rq_trigger_to_num_stages():
    triggers = ['cron', 'pollSCM', 'upstream']
    triggers_found = []
    num_stages = 0
    with open('testjenkinsfile2') as jenkinsfile:
        for line in jenkinsfile:
            line = line.strip('\n')
            # print(line)
            if any(trigger in line for trigger in triggers):
                triggers_found.append(line)
            if 'stage' in line:
                num_stages += 1
    num_stages -= 1
    print(triggers_found, ' ', num_stages)


rq_trigger_to_num_stages()