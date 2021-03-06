import torch
from torch.autograd import Variable as V
import torchvision.models as models
import skimage.io
from torchvision import transforms as trn
from torch.nn import functional as F
import os

# th architecture to use
arch = 'resnet18'

# create the network architecture
model = models.__dict__[arch](num_classes=365)

# load the pre-trained weights
model_weight = '%s_places365.pth.tar' % arch
if not os.access(model_weight, os.W_OK):
    weight_url = 'http://places2.csail.mit.edu/models_places365/%s_places365.pth.tar' % arch
    os.system('wget ' + model_weight)

checkpoint = torch.load(model_weight)
state_dict = {str.replace(k,'module.',''): v for k,v in checkpoint['state_dict'].iteritems()} # the data parallel layer will add 'module' before each layer name
model.load_state_dict(state_dict)
model.eval()

# load the image transformer
centre_crop = trn.Compose([
        trn.ToPILImage(),
        trn.Scale(256),
        trn.CenterCrop(224),
        trn.ToTensor(),
        trn.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# load the class label
file_name = 'categories_places365.txt'
if not os.access(file_name, os.W_OK):
    synset_url = 'https://raw.githubusercontent.com/csailvision/places365/master/categories_places365.txt'
    os.system('wget ' + synset_url)
classes = list()
with open(file_name) as class_file:
    for line in class_file:
        classes.append(line.strip().split(' ')[0][3:])
classes = tuple(classes)

# load the test image
img_name = '12.jpg'
if not os.access(img_name, os.W_OK):
    img_url = 'http://places.csail.mit.edu/demo/12.jpg'
    os.system('wget ' + img_url)
img = skimage.io.imread(img_name)
input_img = V(centre_crop(img).unsqueeze(0), volatile=True)

# forward pass
logit = model.forward(input_img)
h_x = F.softmax(logit).data.squeeze()
probs, idx = h_x.sort(0, True)

# output the prediction
for i in range(0, 5):
    print('{:.3f} -> {}'.format(probs[i], classes[idx[i]]))
