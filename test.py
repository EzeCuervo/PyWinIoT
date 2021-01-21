import wmi
w = wmi.WMI(namespace="root\OpenHardwareMonitor");
temperature_infos = w.Sensor();
for sensor in temperature_infos:
    if sensor.SensorType==u'Temperature':
        if 'CPU Package' in sensor.Name:
            print(sensor.Name);
            print(sensor.Value);
        if 'GPU Core' in sensor.Name:
            print(sensor.Name);
            print(sensor.Value);
#This is a simple code to find the temperature of the CPU using Python.