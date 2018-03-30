#!/bin/sh
on=0
off=0
while :
do
    #Just Add yout Bluetooth address instead FF:FF:FF:FF.FF:FF:FF
    if l2ping -c 2 FF:FF:FF:FF:FF:FF -s 1 &> /dev/null
    then
	   let on=${on}+1
    else
	   let off=${off}+1
    fi

    if [[ $on -eq 5 && $off -le 5 ]]; then
        off=0
        on=0
        #echo "Opened"
        mosquitto_pub -h iot.eclipse.org -m "Open" -t /mc/nodeRed/CastleGate -r
    fi
    if [[ $off -eq 5 && $on -le 5 ]]; then
        on=0
        off=0
        #echo "Closed"
        mosquitto_pub -h iot.eclipse.org -m "Close" -t /mc/nodeRed/CastleGate -r
    fi
done



