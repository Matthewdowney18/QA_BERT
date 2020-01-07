import os
import random
import json
import re
import copy

from bs4 import BeautifulSoup

def remove_duplicates(dataset):
    ids = list()
    new_dataset= list()
    for text in dataset:
        if text["text_id"] not in ids:
            ids.append(text["text_id"])
            new_dataset.append(text)
    return new_dataset



def make_datasets(dataset, filename, train_len, dev_len, test_len, version):
    #dataset = remove_duplicates(dataset)

    train_dataset = {"version": version, "data":{"all"}}
    val_dataset = {"version": version, "data": {}}
    test_dataset = {"version": version, "data": {}}

    for corpus, data in dataset.items():
        dataset_len = len(data)
        test_start = int(dataset_len - dataset_len*test_len/200)
        train_end = int(dataset_len * test_len/200)
        train_dataset["data"] = data[:train_end]
        val_dataset["data"] = data[train_end:test_start]

        for example in data[test_len:]:
            question_types = []
            questions = list(example['paragraphs'][0]['qas'])
            for question in questions:
                type = question["type"]
                if type in question_types:
                    continue
                question_types.append(type)
                text_input = copy.deepcopy(example)
                text_input["paragraphs"][0]['qas'] = [q for q in questions if (q["type"] == type)]
                if question["type"] in test_dataset["data"].keys():
                    test_dataset["data"][type].append(text_input)
                else:
                    test_dataset["data"][type] = [text_input]

    #random.shuffle(dataset)

    train_filename = "{}/train_{}.json".format(filename, version)
    dev_filename = "{}/dev_{}.json".format(filename, version)
    test_filename = "{}/test.json".format(filename, version)

    os.mkdir(filename)

    with open(train_filename, 'w') as fp:
        json.dump(train_dataset, fp)

    with open(dev_filename, 'w') as fp:
        json.dump(val_dataset, fp)

    with open(test_filename, 'w') as fp:
        json.dump(test_dataset, fp)

def clean_string(string):
    patterns = [['\n', ' '], ['\s{2,}',' '], ['"',' ']]
    new_string = string
    for pattern in patterns:
        new_string = re.sub(pattern[0], pattern[1], new_string)
    #new_string = string.split('\n')[1][7:]
    return new_string

def get_answers(answers, id, type):
    result = []
    for answer in answers:
        answer_dict = {}
        answer_dict['id'] = "{}_{}".format(id, answer['id'])
        answer_dict['text'] = clean_string(answer.text)
        #answer_dict['text'] = ""
        if type == "Unanswerable":
            answer_dict["answer_start"] = -1
        else:
            answer_dict["answer_start"] = 0
        result.append(answer_dict)
    return result

def get_qas(text, id):
    qas = []
    for question in text:
        question_dict = {}
        question_dict["id"] = "{}_{}".format(id, str(question["id"]))
        question_dict["type"] = question["type"]
        question_dict["question"] = clean_string(str(question.next_element))

        answers = question.find_all('a')
        answers = [clean_string(answer.text) for answer in answers]
        answers.append("not enough information")
        if question_dict["type"] == "Unanswerable":
            labels = [0, 0, 0, 1]
        else:
            labels = [1, 0, 0, 0]

        answers = random.shuffle(list(zip(answers, labels)))
        for i, (answer, label) in enumerate(answers):
            question_dict["answer_{}".format(i)] = answer
            if label == 1:
                question_dict["label"] = i

        qas.append(question_dict)
    return qas


def get_paragraph(text, id):
    paragraph = {}
    paragraph["qas"] = get_qas(text.find_all("q"), id)
    paragraph["context"] = clean_string(text.find("text_body").text)
    return paragraph

def xml2list(texts):
    dataset = []
    for text in texts:
        text_data = {}
        text_data["text_id"] = text['id']
        text_data["author"] = clean_string(text.find("author").text)
        text_data["title"] = clean_string(text.find("title").text)
        text_data["url"] = clean_string(text.find("url").text)
        text_data["paragraphs"] = [get_paragraph(text, text_data["text_id"])]
        dataset.append(text_data)
    return dataset

def main():
    project_file = os.getcwd()
    version = '2'
    dataset_dir = "{}/data/raw_data/".format(project_file)
    output_dir = "{}/data_{}".format(project_file, version)
    data = {}

    for dataset in os.listdir(dataset_dir):
        handle = open(dataset_dir + dataset, 'r')
        soup = BeautifulSoup(handle,'lxml')

        texts = soup.find_all('text')
        data[dataset.split(".")[0] ] = xml2list(texts)

    make_datasets(data, output_dir, 140, 30, 30, version)


if __name__ == '__main__':
    main()