import measpy.signal as sig
import measpy.measurement as mes
from measpy.audio import audio_run_measurement, audio_get_devices
import sounddevice as sd
import matplotlib.pyplot as plt
import numpy as np
import copy
import time

def printDistinctDevices():
    devices = []
    ban_devices = []
    for oneDev in sd.query_devices():
        if oneDev["name"] not in devices:
            devices.append(oneDev["name"])
        elif oneDev["name"] not in ban_devices:
            ban_devices.append(oneDev["name"])

    for oneDev in devices:
        if oneDev not in ban_devices:
            print("- ",oneDev)

def oneDevice():
    devices = audio_get_devices()
    for oneDev in devices:
        return oneDev

def simpleMeasure():
    # l = audio_get_devices()
    # print(l.get())

    # for device in sd.query_devices(): 
    #     if "Casque" in device["name"]:
    #         print("plpl",device) 

    Fs=1000
    addr = np.array([0,1,2,4,8,16,32])
    # sout = sig.Signal.noise(fs=44100, freq_min=20, freq_max=20000, dur=5)
    sout = sig.Signal(desc = "sensor addresses", fs=Fs, raw=addr, type=sig.SignalType.DIGITAL)
    sin1 = sig.Signal(desc = 'Pressure', dbfs=5.0, cal=1.0, unit="Pa")
    sin2 = sig.Signal(desc = 'Acceleration', dbfs=5.0, cal=0.1, unit="m*s**(-2)")

    M1 = mes.Measurement(
        out_sig = [sout],
        out_map = [1],
        in_sig = [sin1,sin2],
        in_map = [1,2],
        dur = 5,
        device_type = 'audio'
    )

    print("STAAAAARTIIIING")
    audio_run_measurement(M1)
    print("EEEEEENNNDEEEED")

    print(f"type: {type(M1.in_sig[0])} - len: {len(M1.in_sig[0])}")
    print(f"type: {type(M1.in_sig[0].raw)} - len: {len(M1.in_sig[0].raw)}")

    print("presentation : ",M1.in_sig[0])

    print("raw : ",M1.in_sig[0].raw)


    M1.in_sig[0].plot()
    plt.show()

# !!! IMPORTANT WORK !!!

def scaleAddresses(addr: list, fb: int, fs: int)-> tuple[list,int]:
    """
    Add/duplicate addresses from addr list to match to difference frequency of fs and fb.

    :param addr: list of addresses, digital values
    :type addr: list
    :param fb: frequency of expected return measurement
    :type fb: int
    :param fs: frequency of the data acquisition on the card
    :type fs: int
    :return: scaled address list and new frequency fs to send to the card
    :rtype: tuple (addr,fs)
    """
    addr = copy.deepcopy(addr)
    nbAdr = len(addr)
    nbIt = int(round(fs/(nbAdr*fb)))
    for it in range(nbAdr):
        addr[it*nbIt:it*nbIt+1] *= nbIt
    # return addr,fs/(nbAdr*nbIt)
    return addr,(nbAdr*nbIt*fb)

def matchResultsBis(sigValues: sig.Signal, sigAddr: sig.Signal, rate: float)->sig.Signal:
    """
    :param sigValues: signal acquired
    :type sigValues: measpy.signal.Signal
    :param sigAddr: digital signal of addresses sent
    :type sigAddr: measpy.signal.Signal
    :param rate: rate of values to keep per address, must be between 0 and 1
    :type rate: float
    :return: Clean signal with one value per time
    """
    # if(len(sigValues.values) != len(sigAddr.values)):
    #     raise ValueError(f"sigValues and sigAddr do not have the same length. nb values : {len(sigValues.values)}, nb addr : {len(sigAddr.values)}")
    if rate<0 or rate>1:
        raise ValueError(f"rate should be between 0 and 1. currently : {rate}")

    resultSig_raw = []
    resultAdr_raw = []
    from_one_sensor = []
    sensor = None
    for i in range(len(sigValues.values)):
        if sigAddr.values[i%len(sigAddr.values)] != sensor:
            if len(from_one_sensor) > 0:
                # Only look at the specified rate of values centered and save the mean value.
                # print(f"from_one_sensor before : {from_one_sensor}")
                diff = int(round((1-rate)*len(from_one_sensor)/2))
                # print(f"diff : {diff}")
                from_one_sensor = from_one_sensor[diff:-diff]
                # print(f"from_one_sensor after : {from_one_sensor}")
                resultSig_raw.append(sum(from_one_sensor)/len(from_one_sensor))
                resultAdr_raw.append(sensor)
                # print(f"new ! {sum(from_one_sensor)/len(from_one_sensor)}")
            # Initiate a from a new sensor
            from_one_sensor = []
            sensor = sigAddr.values[i%len(sigAddr.values)]
        from_one_sensor.append(sigValues.values[i])

    sigResult = sig.Signal.pack([
        sig.Signal(
            desc="Addresses",
            cal=sigValues.cal,
            dbfs=sigValues.dbfs,
            raw=np.array(resultAdr_raw),
            type=sig.SignalType.DIGITAL
            # NEED TO ADD FS
        ),
        sig.Signal(
            desc="Values",
            unit=sigValues.unit,
            cal=sigValues.cal,
            dbfs=sigValues.dbfs,
            raw=np.array(resultSig_raw)
            # NEED TO ADD FS
        )
    ])
    return sigResult

def matchResults(sigValues: sig.Signal, sigAddr: sig.Signal, rate: float)->sig.Signal:
    """
    :param sigValues: signal acquired
    :type sigValues: measpy.signal.Signal
    :param sigAddr: digital signal of addresses sent
    :type sigAddr: measpy.signal.Signal
    :param rate: rate of values to keep per address, must be between 0 and 1
    :type rate: float
    :return: Clean signal with one value per time
    """
    # if(len(sigValues.values) != len(sigAddr.values)):
    #     raise ValueError(f"sigValues and sigAddr do not have the same length. nb values : {len(sigValues.values)}, nb addr : {len(sigAddr.values)}")
    if rate<0 or rate>1:
        raise ValueError(f"rate should be between 0 and 1. currently : {rate}")

    resultSig_raw = { adr:[] for adr in sigAddr.values }
    from_one_sensor = []
    sensor = None
    for i in range(len(sigValues.values)):
        if sigAddr.values[i%len(sigAddr.values)] != sensor:
            if len(from_one_sensor) > 0:
                # Only look at the specified rate of values centered and save the mean value.
                # print(f"from_one_sensor before : {from_one_sensor}")
                diff = int(round((1-rate)*len(from_one_sensor)/2))
                # print(f"diff : {diff}")
                if diff != 0:
                    from_one_sensor = from_one_sensor[diff:-diff]
                # print(f"from_one_sensor after : {from_one_sensor}")
                resultSig_raw[sensor].append(sum(from_one_sensor)/len(from_one_sensor))
                # print(f"new ! {sum(from_one_sensor)/len(from_one_sensor)}")
            # Initiate a from a new sensor
            from_one_sensor = []
            sensor = sigAddr.values[i%len(sigAddr.values)]
        from_one_sensor.append(sigValues.values[i])

    sizes = []
    for vals in resultSig_raw.values():
        sizes.append(len(vals))
    sigList = []
    for adr,vals in resultSig_raw.items():
        sigList.append(
            sig.Signal(
                desc=adr,
                cal=sigValues.cal,
                dbfs=sigValues.dbfs,
                raw=np.array(vals[:min(sizes)])
            )
        )
    return sig.Signal.pack(sigList)

def matchResultsSpeedUp(sigValues: sig.Signal, sigAddr: sig.Signal, rate: float)->sig.Signal:
    """
    :param sigValues: signal acquired
    :type sigValues: measpy.signal.Signal
    :param sigAddr: digital signal of addresses sent
    :type sigAddr: measpy.signal.Signal
    :param rate: rate of values to keep per address, must be between 0 and 1
    :type rate: float
    :return: Clean signal with one value per time
    """
    # if(len(sigValues.values) != len(sigAddr.values)):
    #     raise ValueError(f"sigValues and sigAddr do not have the same length. nb values : {len(sigValues.values)}, nb addr : {len(sigAddr.values)}")
    if rate<0 or rate>1:
        raise ValueError(f"rate should be between 0 and 1. currently : {rate}")

    resultSig_raw = { adr:[] for adr in sigAddr.values }
    nb = len(sigAddr.values)/len(resultSig_raw.keys())
    diff = int(round((1-rate)*nb/2))

    print(resultSig_raw)
    print("nb: ",nb)
    print("it: ",int(len(sigValues.values)/nb))
    from_one_sensor = []
    for i in range(int(len(sigValues.values)/nb)):
        from_one_sensor = sigValues.values[int(round(i*nb)):int(round((i+1)*nb))]
        if diff != 0:
            from_one_sensor = from_one_sensor[diff:-diff]
        sensor = sigAddr.values[int((i*nb)%len(sigAddr.values))]
        resultSig_raw[sensor].append(sum(from_one_sensor)/len(from_one_sensor))

    sizes = []
    for vals in resultSig_raw.values():
        sizes.append(len(vals))
    sigList = []
    for adr,vals in resultSig_raw.items():
        sigList.append(
            sig.Signal(
                desc=adr,
                cal=sigValues.cal,
                dbfs=sigValues.dbfs,
                raw=np.array(vals[:min(sizes)])
            )
        )

    return sig.Signal.pack(sigList)

def matchResultsSpeedUpV2(sigValues: sig.Signal, sigAddr: sig.Signal, rate: float)->sig.Signal:
    """
    :param sigValues: signal acquired
    :type sigValues: measpy.signal.Signal
    :param sigAddr: digital signal of addresses sent
    :type sigAddr: measpy.signal.Signal
    :param rate: rate of values to keep per address, must be between 0 and 1
    :type rate: float
    :return: Clean signal with one value per time
    """
    # if(len(sigValues.values) != len(sigAddr.values)):
    #     raise ValueError(f"sigValues and sigAddr do not have the same length. nb values : {len(sigValues.values)}, nb addr : {len(sigAddr.values)}")
    if rate<0 or rate>1:
        raise ValueError(f"rate should be between 0 and 1. currently : {rate}")

    resultSig_raw = { adr:[] for adr in sigAddr.values }
    nb = len(sigAddr.values)/len(resultSig_raw.keys())
    diff = int(round((1-rate)*nb/2))

    print(resultSig_raw)
    print("nb: ",nb)
    print("it: ",int(len(sigValues.values)/nb))
    from_one_sensor = []
    for i in range(int(len(sigAddr.values)/nb)):
        

        from_one_sensor = sigValues.values[int(round(i*nb)):int(round((i+1)*nb))]
        if diff != 0:
            from_one_sensor = from_one_sensor[diff:-diff]
        sensor = sigAddr.values[int((i*nb)%len(sigAddr.values))]
        resultSig_raw[sensor].append(sum(from_one_sensor)/len(from_one_sensor))

    sizes = []
    for vals in resultSig_raw.values():
        sizes.append(len(vals))
    sigList = []
    for adr,vals in resultSig_raw.items():
        sigList.append(
            sig.Signal(
                desc=adr,
                cal=sigValues.cal,
                dbfs=sigValues.dbfs,
                raw=np.array(vals[:min(sizes)])
            )
        )

    return sig.Signal.pack(sigList)


# !!! TEST METHODS !!!

def testScaleAddresses():
    addresses = [0,1,2,4,8]

    new_addr,new_fs = scaleAddresses(addr=addresses, fb=300, fs=20000)

    print(addresses)
    print(new_addr)
    print(f"new nb adr : {len(new_addr)} - new fs : {new_fs} Hz")

def testMatchResults():
    import time
    # ar = np.array([1,2,3,4,5,6,7,8])
    # for i in range(len(ar)):
    #     print(i," - ",ar[i])
    FB = 300
    FS = 20000
    FS = 1000000

    adrs = [0,1,2,4,8,16,32]
    adrs = list(range(0,64))
    # adrs = list(range(64))
    # adrs = [0,1,2,4]
    adrs,NFS = scaleAddresses(adrs, FB, FS)
    adr_sig = sig.Signal(fs=FS,raw=np.array(adrs),type=sig.SignalType.DIGITAL)

    import random
    vals = np.array([random.random()*100 for i in range(500000)])
    val_sig = sig.Signal(fs=FB,raw=vals)

    # print(adr_sig.raw)
    # print(scaleAddresses(adrs, FS, FB))
    t0 = time.time()
    res = matchResultsSpeedUp(sigValues=val_sig, sigAddr=adr_sig, rate=1)
    t1 = time.time()

    print(f"matchResults took {t1-t0}s")
    # print(res)
    # for adr,val in res.items():
    #     print(f"{adr} : {val[:5]}...")

    print(type(res))
        
    print(len(res))
    
    print(f"matchResults took {t1-t0}s")
    # res.plot()
    # plt.show()  

def readH5(filepath):
    thesig: sig.Signal = sig.Signal.from_hdf5(filepath,"in_sigs")
    print(thesig)
    print(type(thesig))

    # print(thesig[4])
    # sigLiiist = thesig[4:]
    # print(type(sigLiiist))
    # sigMerged = sig.Signal.pack(sigLiiist)
    # print(sigMerged)
    # sigMerged.plot()
    
    # sigMerged = sig.Signal.pack(thesig)

    plt.show()

if __name__ == "__main__":
    print("start main")

    # printDistinctDevices()

    # print(oneDevice())

    # testScaleAddresses()
    testMatchResults()
    #
    # testPlot()

    # readH5("C:\\Users\\cleme\\OneDrive\\Documents\\Stage ENSTA\\measpy\\MESMESURES.hdf5")

    print("end main")
