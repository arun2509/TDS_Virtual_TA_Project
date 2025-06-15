import numpy as np
allow_pickle = True

data = np.load("embeddings_data.npz")
for key in data.files:
    allow_pickle = True
    print(key, data[key].shape)
