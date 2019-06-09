# hassUnifiBlockSwitch
A Home Assistant custom component that allows for block/unblocking a Group on a Ubiquiti Unifi Controller

Summary: 

I needed the ability to turn off internet access to a child's devices, they had 4 of them. So I wrote this HASS component to allow me to flip them on or off with a single button (created a "group" of switches), or I can fine tune and allow select devices on or off if I want. Also allows me to use Automations on the HASS server to turn off internet at specified times, and turn back on automatically. This is my first HASS custom component, feel free to improve.

Install:

1.) Place the project files in your config\custom_components\unifi_device_block folder. Create the folder if needed.

2.) On your Ubiquiti Controller create a user with read/write permissions (needed to block/unblock users)

3.) Inside the Ubiquit Controller place the devices you want control over in HASS inside a group. (Click on the device, then in the details window you can assign it to a group). The name of this group will be used in step 4.

4.) Add to your Hass configuration.yaml:
  
    switch:
      - platform: unifi_device_block
        host: "Unifi Controller IP Address"
        username: "UbiquitiUsername"
        password: "UbiquitiPassword"
        port: 8443
        user_group_name: "UbiquitiGroupName"

5.) Restart your Hass server, you should now have "switches" representing each of the devices in the group. Toggling the switch to off will block the device from connecting to the network, toggling the switch on will allow the device to reconnect.

Oddities:
1.) I have had two occasions where unblocked devices seemed to be assigned incorrect IP addresses by the USG. I had to restart the USG to get it fixed, but I haven't opened a support ticket for this yet. Still trying to see if I can reproduce.

Change Log: 
2019-05-31: Major reconfiguration to accomodate changes in Home Assitant V0.92. 
