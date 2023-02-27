# Visualizations

## Blender

### Dependencies

- `bpy`
- `rowan`
- `numpy` 
- `yaml` 

### Output
- Takes pictures from robots' perspectives
- Saves pictures in working directory in `simulation_results/<date-and-time>/Raw-Dataset` with the following folder structure

    ```
    Raw-Dataset
    ├── cf1
    │   ├── calibration.yaml
    │   ├── cf0.csv
    │   ├── cf0_00000.jpg
    │   ├── cf0_00001.jpg
    │   └── ...
    ├── ...
    └── cfn
        ├── calibration.yaml
        ├── cfn.csv
        ├── cfn_00000.jpg
        ├── cfn_00001.jpg
        └── ...
    ```
    where `<name>.csv` contains the states in world coordinates of the camera or crazyflie, `calibration.yaml` contains the calibration information of the cameras and 
    `<name>_<frame>.jpg` is the `<frame>`th image taken from `<names>`'s perspective. If a robot is configured to not carry a camera, only `<name>.csv` will be recorded. 
- In order to use it, you need to add `blender` to the list of visualizations in `crazyswarm2/crazyflie/config/server.yaml` and run 

    ```sh
    ros2 launch crazyflie launch.py backend:=sim
    ```

### Configuration
- Crazyflies to appear in scene are defined in `crazyflie/config/crazyflies.yaml` 
- In `crazyflie/config/server.yaml` you **must** set the following parameters, unless stated otherwise:
    * `enabled: boolean`, enables or disables blender visualization in simulator
    * `fps: float`, frames per second rate of all cameras  
    * `auto_yaw: boolean`, enables or disables auto-yaw (optional, defaults to `false` if not set)
        - `radps: float`, radians per second
    * for every robot in `cf_cameras`:
        - `calibration`
            * `camera_matrix: list[float]`, camera matrix as list in row-major order
            * `dist_coeff: list[float]` (has no effect at the moment, defaults to $(0,0,0,0,0)^\top$)
            * `tvec: list[float]` (has no effect at the moment, defaults to $(0,0,0)^\top$)
            * `rvec: list[float]` 
- Example configuration  

    ```yaml
    blender:
      enabled: true
      auto_yaw:     # constant yaw rotation applied to cf_cameras only
        enabled: true
        radps: 5   # radians per second
      fps: 1           # frames per second
      cycle_bg: false  # if true, pictures will cycle through different environemt background images (useful for synthetic image generation). Otherwise a single environment background image will be used
      cf_cameras:      # names of crazyflies with cameras on them if enabled in `crazyflies.yaml`
        cf231:
          calibration:
            camera_matrix: [170.0, 0.0, 160.0, 0.0, 170.0, 160.0, 0.0, 0.0, 1.0] # matrix in row-major order
            dist_coeff: [0,0,0,0,0]
            tvec: [0,0,0]
            rvec: [1.2092,-1.2092,1.2092]   # 0 deg tilt
        cf5:
          calibration:
            camera_matrix: [170.0, 0.0, 160.0, 0.0, 170.0, 160.0, 0.0, 0.0, 1.0] # matrix in row-major order
            dist_coeff: [0,0,0,0,0]
            tvec: [0,0,0]
            rvec: [ 0.61394313, -0.61394313,  1.48218982]   # 45 deg tilt
        cf6:
          calibration:
            camera_matrix: [170.0, 0.0, 160.0, 0.0, 170.0, 160.0, 0.0, 0.0, 1.0] # matrix in row-major order
            dist_coeff: [0,0,0,0,0]
            tvec: [0,0,0]
            rvec: [0.0,0.0,1.5707963267948966]    # 90 deg tilt
    ```

### Acknowledgments 

- All background images are in the public domain (CC0 license) and were sourced from [polyhaven.com](https://polyhaven.com/) 
- The crazyflie model used is under an MIT license and was modified and sourced from [https://github.com/bitcraze/crazyflie-simulation](https://github.com/bitcraze/crazyflie-simulation)

