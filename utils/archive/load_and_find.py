from PIL import Image
import pandas as pd
import csv


count_target_photos = 2


# Need fix

def prepare_data(k):
    table = []
    for i in range(136):
        # print(i)
        with open(f'target/archive/table_{i}.csv', 'r') as f:
            read = csv.reader(f)
            for row in read:
                del row
                break
            for row in read:
                table.append([row[x] if x == 0 else float(row[x]) for x in [0, k]])
    with open(f'target/archive/_all_{k}.csv', 'w', newline='') as file:
        write = csv.writer(file, delimiter=',')
        for x in table:
            write.writerow(x)
    # print(table)


prepare_data(1)
prepare_data(2)

# quit()

for i in range(1, count_target_photos + 1):
    data = {}
    with open(f'target/archive/_all_{i}.csv', 'r') as f:
        read = csv.reader(f)
        for row in read:
            data[row[0]] = row[1]

    list_d = list(data.items())
    list_d.sort(key=lambda i: i[1])
    print(list_d[:10])







