from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
from torch.utils.data import DataLoader
from torchvision import datasets
import numpy as np
import pandas as pd
import os
from PIL import Image


workers = 0 if os.name == 'nt' else 4


device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
print('Running on device: {}'.format(device))


mtcnn = MTCNN(image_size=160, margin=0)
resnet = InceptionResnetV1(pretrained='vggface2').eval()


def collate_fn(x):
    return x[0]


dataset = datasets.ImageFolder('data')
dataset.idx_to_class = {i:c for c, i in dataset.class_to_idx.items()}


loader = DataLoader(dataset, collate_fn=collate_fn, num_workers=workers)


g_counter = 0


def target():
    aligned = []
    names = []
    for i in range(2):
        x = Image.open(f'target/{i}.jpg')
        x_aligned, prob = mtcnn(x, return_prob=True)
        if x_aligned is not None:
            # print('Face detected with probability: {:8f}'.format(prob))
            aligned.append(x_aligned)
            names.append(f'target_{i}')
    return aligned, names


aligned, names = target()


for x, y in loader:
    if len(aligned) == 50:
        print(g_counter)
        aligned = torch.stack(aligned).to(device)
        embeddings = resnet(aligned).detach().cpu()
        dists = [[(e1 - e2).norm().item() for e2 in embeddings] for e1 in embeddings]
        pd.DataFrame(dists, columns=names, index=names).to_csv(f'target/table_{g_counter}.csv')
        g_counter += 1
        aligned, names = target()
    try:
        x_aligned, prob = mtcnn(x, return_prob=True)
        if x_aligned is not None:
            # print('Face detected with probability: {:8f}'.format(prob), len(aligned))
            aligned.append(x_aligned)
            names.append(dataset.idx_to_class[y])
    except:
        pass


aligned = torch.stack(aligned).to(device)
embeddings = resnet(aligned).detach().cpu()

dists = [[(e1 - e2).norm().item() for e2 in embeddings] for e1 in embeddings]
print(pd.DataFrame(dists, columns=names, index=names))
# pd.DataFrame(dists, columns=names, index=names).to_csv('target/table.csv')








