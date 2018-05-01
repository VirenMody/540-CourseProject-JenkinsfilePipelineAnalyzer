

def occurrences_in_file(filename, word_to_search):
    jenkinsfile = open(filename, 'r').read()
    if jenkinsfile.count('triggers') > 0:
        print('The number of stages in this Jenkinsfile is: ', jenkinsfile.count(word_to_search))

