import numpy as np
import json
import time
import os
np.set_printoptions(suppress=True)

def template():
    output = {
      "intrinsics":{ 
        "Fx": 0.0,
        "Fy": 0.0,
        "Cx": 0.0,
        "Cy": 0.0,
        "K1": 0.0,
        "K2": 0.0,
        "K3": 0.0,
        "K4": 0.0,
        "K5": 0.0,
        "K6": 0.0,
        "P1": 0.0,
        "P2": 0.0
        },
        "camera_model": "radial"
    }
    return output

def undistort(file):
    # Fisheye to Radial intrinsics 

    cameraName = file.split('/')[-1].split('.')[0]
    print(file)
    with open(file, 'r') as stream:
        camera_intrinsics = json.load(stream)

    if camera_intrinsics['camera_model'] == 'radial':
        json_object = json.dumps(camera_intrinsics, indent=2)
    
    else: 
        Cx = camera_intrinsics["intrinsics"]["Cx"]
        Cy = camera_intrinsics["intrinsics"]["Cy"]
        Fx = camera_intrinsics["intrinsics"]["Fx"]
        Fy = camera_intrinsics["intrinsics"]["Fy"]
        K1 = camera_intrinsics["intrinsics"]["K1"]
        K2 = camera_intrinsics["intrinsics"]["K2"]
        K3 = camera_intrinsics["intrinsics"]["K3"]
        K4 = camera_intrinsics["intrinsics"]["K4"]

        intrinsics = np.array([[Fx, 0, Cx],
                [0,  Fy,Cy],
                [0,  0, 1]])
        distortion = np.array([K1, K2, K3, K4])

        #scale the intrinsics to keep the FOV
        scaled_K = 1*intrinsics
        offset_h_1 = 300
        offset_h_2 = 700
        if cameraName == "BPillarLeftCamera" or cameraName == 'BPillarRightCamera':
            offset_h_1 = 300
            offset_h_2 = 300
        scaled_K[0][2] = intrinsics[0][2]*2
        scaled_K[1][2] = intrinsics[1][2]*2-offset_h_1
        output = template()
        output['intrinsics']['Fx'] = scaled_K[0][0]
        output['intrinsics']['Fy'] = scaled_K[1][1]
        output['intrinsics']['Cx'] = scaled_K[0][2]
        output['intrinsics']['Cy'] = scaled_K[1][2]
        
        # Serializing json
        json_object = json.dumps(output, indent=2)

    # Writing to sample.json
    try:
        cameraName = cameraName.replace('_fisheye', '')
    except:
        pass

    newname = cameraName + ".json"
    with open("output/"+newname, "w") as outfile:
        outfile.write(json_object)
    
    return newname

def allowed_files(filename):
    cams = [
        'WingMirrorRight.json',
        'WingMirrorLeft.json',
        'SVCRight.json',
        'SVCLeft.json',
        'SVCCenterRear.json',
        'SVCCenterFront.json',
        'RearNarrowCamera.json',
        'FrontWideCamera.json',
        'FrontNarrowCamera.json',
        'BPillarRightCamera.json',
        'BPillarLeftCamera.json',
    ]
    return True if filename in cams else False

def remove_old_files(path):
    current_time = time.time()
    for f in os.listdir(path):
        creation_time = os.path.getctime(f)
        if (current_time - creation_time) // (24 * 3600) >= 7:
            os.unlink(f)
            print('{} removed'.format(f))