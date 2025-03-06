import pyvisa
import logging
import time
import datetime

#external parameters for 2400
currents = [ 0,0.001,0.0015, 0.002, 0.0025, 0.003,0.0019,0] #list of current values
cur_str = ",".join([str(x) for x in currents]) 
#The selected range affects both accuracy of the voltage measurement as well as the maximum voltage that can be measured
#Range is selected by specifying the approximate source magnitude that you will be using. The instrument will then go to the lowest range that can accommodate that level
Irange = 0.003 #2400 source range: 1μA, 10μA, 100μA, 1mA, 10mA, 100mA, 1A.
Vrange = 30 #2400 sense range: 200mV, 2V, 20V, 200V.
lim2400 = 120 #set compliance limit. 2400 cannot source levels that exceed this specified limit.
# You cannot set compliance less than 0.1% of the present measurement range (Vrange)

#external parameters for 2182
speed = 0.01 #nplc of 2182, from 0.01 to 50 (60 for 60Hz system).Time of 1 measurement = NPLC/50 in seconds
Vrange2 = 30 #2182 sense range: 10mV, 100mV, 1V, 10V, 100V.
T = 0.001 # delay time for 2182 between receiving a trigger from 2400 and measuring, from 0 to 999999.999 (sec)

N = 10 #total amount of measurements 
#logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("TEST")

#initialization of devices
rm = pyvisa.ResourceManager()
k2400 = rm.open_resource("GPIB0::3::INSTR") #gpib number of 2400 is 3
k2182 = rm.open_resource("GPIB0::7::INSTR") #gpib number of 2182 is 7
k2400.write("*rst;") #returns 2400 to default conditions 
k2182.write("*rst;") #returns 2182 default conditions

#set source
k2400.write("SOUR:FUNC CURR") #2400 is sourcing current
logging.info(k2400.query(":SYST:ERR?")) 

k2400.write(f"SOUR:CURR:RANG {Irange}") #2400 sourcing current range
logging.info(k2400.query(":SYST:ERR?")) 
k2400.write("SOUR:CURR:MODE LIST") #I-source mode list (2400 will source currents as specified in the list)
logging.info(k2400.query(":SYST:ERR?")) 
k2400.write(f"SOUR:LIST:CURR {cur_str}") #current values in the cycle as in the list cur_str
logging.info(k2400.query(":SYST:ERR?"))  
k2400.write(f"TRIG:COUN {len(currents)}") #amount of current values in a cycle
logging.info(k2400.query(":SYST:ERR?"))
k2400.write("SOUR:DEL:AUTO 0") # auto delay off, 0  seconds between sourcing and measuring for 2400
###k2400.write("SOUR:DEL 0") ###############################
logging.info(k2400.query(":SYST:ERR?"))

#set function on 2400
k2400.write("SENS:FUNC 'VOLT:DC'") #2400 measures voltage
logging.info(k2400.query(":SYST:ERR?")) 
k2400.write(f"SENS:VOLT:PROT {lim2400}") #2400 voltage compliance limit
logging.info(k2400.query(":SYST:ERR?")) 
k2400.write(f"SENS:VOLT:RANG {Vrange}") # 2400 measuring voltage range
logging.info(k2400.query(":SYST:ERR?")) 
k2400.write("SENS:VOLT:NPLC 0.01") #time of 1 measurement (NPLC/50 in seconds) 
#(set to minimum because 2400 does not need to measure with high accuracy but needs maximum speed) 
logging.info(k2400.query(":SYST:ERR?")) 


#set function on 2182
k2182.write("SENS:FUNC 'VOLT'") #2182 measures voltage
logging.info(k2182.query(":SYST:ERR?")) 
k2182.write("SENS:CHAN 1") #measures channel 1 (voltage)
logging.info(k2182.query(":SYST:ERR?")) 
k2182.write(f"SENS:VOLT:NPLC {speed}") #2182 time of 1 measurement
logging.info(k2182.query(":SYST:ERR?"))  
k2182.write(f"SENS:VOLT:CHAN1:RANG {Vrange2}") #2182 measuring voltage range 
logging.info(k2182.query(":SYST:ERR?"))  

#set arm layer 2400
k2400.write("ARM:SOUR TLINk") #each cycle (of sourcing values from the cur_str list and measuring the output) will start after a trigger from 2182 (via triggerlink)
logging.info(k2400.query(":SYST:ERR?"))
k2400.write("ARM:COUNT INF") # without ABORT the cycles will repeat an infinite amount of times 
logging.info(k2400.query(":SYST:ERR?")) 
k2400.write("ARM:DIR SOUR ") #the first cycle will start without any trigger
logging.info(k2400.query(":SYST:ERR?")) 

#set trigger layer 2400
k2400.write("TRIG:OUTP SOUR") #2400 will send a trigger (to 2182) after it sourced a current from the cur_str list
logging.info(k2400.query(":SYST:ERR?")) 
k2400.write("TRIG:SOUR TLINK") #2400 will receive triggers (from 2182) via triggerlink, after he receives one he will change the current to the next value in the list
logging.info(k2400.query(":SYST:ERR?")) 
k2400.write("TRIG:DIR SOUR") #2400 will source the first value in the cur_str list without any trigger
logging.info(k2400.query(":SYST:ERR?")) 


#set trigger layer 2182
k2182.write("TRIG:SOUR EXT") #2182 will receive trigger from 2400 and start measuring 
logging.info(k2182.query(":SYST:ERR?"))
k2182.write("TRIG:COUN INF") #the amount of measurements is not limited 
logging.info(k2182.query(":SYST:ERR?"))
k2182.write("TRIG:DEL:AUTO 0") # auto delay off 
logging.info(k2182.query(":SYST:ERR?"))
k2182.write(f"TRIG:DEL {T}") #after receiving a trigger 2182 will wait T sec before starting the measurement  
logging.info(k2182.query(":SYST:ERR?"))

#turning off both displays 
k2182.write("DISP:ENAB 0")
logging.info(k2182.query(":SYST:ERR?"))
k2400.write("DISP:ENAB 0")
logging.info(k2182.query(":SYST:ERR?"))

k2182.write("INIT") #2182 starts waiting for a trigger 
k2400.write("OUTP ON") #turning on output on 2400
k2400.write("INIT") #starting the current function and cycles on 2400


for index in range(N):
	#time.sleep(3)
	value = k2182.query("DATA:FRESH?") #Returns a new reading, 1 of each measurement 
	#print(value)
	print(f"{datetime.datetime.now()}: {value}")
k2400.write("ABORT") #after reading N measurements aborts the whole cycle
k2400.write("OUTP off") #turns off output on 2400




