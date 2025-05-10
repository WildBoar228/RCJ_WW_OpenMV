import sensor


sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
#sensor.set_auto_gain(False)  # must be turned off for color tracking
#sensor.set_auto_whitebal(False)  # must be turned off for color tracking

##sensor.set_gainceiling(128)
#sensor.set_contrast(0)
#sensor.set_brightness(0)
#sensor.set_saturation(0)
##sensor.set_quality(100)
#sensor.set_auto_exposure(False, exposure_us=10000)

 # Setup for manual gain, exposure, and white balance
sensor.set_auto_gain(False, gain_db=3) # gain in db
sensor.set_auto_whitebal(False)
sensor.set_auto_exposure(False, exposure_us=10000) # exposure in us

 # Setup contrast, brightness and saturation
sensor.set_contrast(3) # range -3 to +3
sensor.set_brightness(0) # range -3 to +3
sensor.set_saturation(0) # range -3 to +3

# Disable night mode (auto frame rate) and black level calibration (BLC)
sensor.__write_reg(0x0E, 0b00000000) # Disable night mode
sensor.__write_reg(0x3E, 0b00000000) # Disable BLC

# Set White Balance values manually
sensor.__write_reg(0x01, 255) # Blue Gain for White Balance
sensor.__write_reg(0x02, 120) # Red Gain for White Balance
sensor.__write_reg(0x03, 120) # Green Gain for White Balance

## Restore to default values (these are changed before manual mode takes effect)
#sensor.__write_reg(0x2D, 0b00100000) # LSB Insert Dummy Rows (Set to Default 0x00)
#sensor.__write_reg(0x2E, 0b00100000) # MSB Insert Dummy Rows (Set to Default 0x00)

sensor.__write_reg(0x35, 0b10000000) # AD Offset B Chan (Set to Default 0x80)
sensor.__write_reg(0x36, 0b10000000) # AD Offset R Chan (Set to Default 0x80)
sensor.__write_reg(0x37, 0b10000000) # AD Offset Gb Chan (Set to Default 0x80)
sensor.__write_reg(0x38, 0b10000000) # AD Offset Gr Chan (Set to Default 0x80)

sensor.__write_reg(0x39, 0b10000000) # B channel offset (Set to Default 0x80)
sensor.__write_reg(0x3A, 0b10000000) # R channel offset (Set to Default 0x80)
sensor.__write_reg(0x3B, 0b10000000) # Gb channel offset (Set to Default 0x80)
sensor.__write_reg(0x3C, 0b10000000) # Gr channel offset (Set to Default 0x80)
