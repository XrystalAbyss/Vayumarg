import h5py

path = "data/processed/satellite/crops/BIPARJOY_20230612_2358_MULTICHANNEL.h5"
with h5py.File(path, "r") as f:
    print("Keys in crop:", list(f.keys()))
    for k in f.keys():
        obj = f[k]
        if isinstance(obj, h5py.Dataset):
            print(f"Dataset {k}: shape={obj.shape}, dtype={obj.dtype}")
        elif isinstance(obj, h5py.Group):
            print(f"Group {k}: subkeys={list(obj.keys())}")
            for subk in obj.keys():
                subobj = obj[subk]
                if isinstance(subobj, h5py.Dataset):
                    print(f"  Dataset {k}/{subk}: shape={subobj.shape}, dtype={subobj.dtype}")
