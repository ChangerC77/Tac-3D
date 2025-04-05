import cv2
import os
import sys
import time

def TakePictures(device, fileName = '', dirPath='.'):
    framesSkip = 30
    FPS = 999
    interval_ms =  1000.0 / FPS - 1;
    manualExposure = -6
    inputSrc = device
    wname = 'camera'
    
    if sys.platform.startswith('win'):
        cap = cv2.VideoCapture(int(inputSrc), cv2.CAP_DSHOW)
    elif sys.platform.startswith('linux'):
        cap = cv2.VideoCapture(int(inputSrc), cv2.CAP_V4L2)
    else:
        print('Unknow System')
        return
        
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

    # 打开自动曝光
    if sys.platform.startswith('win'):
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1.0)
    elif sys.platform.startswith('linux'):
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3.0)
    
    cap.set(cv2.CAP_PROP_AUTO_WB, 1.0) 
    
    # 打开自动白平衡
    cap.set(cv2.CAP_PROP_AUTO_WB, 1.0)
    for i in range(framesSkip):
        cap.read();
        time.sleep(interval_ms / 1000);

    # 关闭自动曝光
    # 并设置手动曝光参数
    if sys.platform.startswith('win'):
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.0) 
        cap.set(cv2.CAP_PROP_EXPOSURE, manualExposure)
    elif sys.platform.startswith('linux'):
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1.0) # 关闭自动曝光
        cap.set(cv2.CAP_PROP_EXPOSURE, 10000 * 2**manualExposure)

##    cap.set(cv2.CAP_PROP_BRIGHTNESS, 1)
    cap.set(cv2.CAP_PROP_GAMMA , 7)
    fnIdx = 1
    recordFlag = False
    n = 1
    goon, frame = cap.read()
    # print('size: %d x %d' % (frame.shape[1], frame.shape[0]))
    cv2.namedWindow(wname, 0)
    cv2.imshow(wname, frame)
    key = cv2.waitKey(2)
    dt = interval_ms / 1000
    t0 = time.time()
    
    while goon:
        if recordFlag:
            videoWriter.write(frame)
        if cv2.getWindowProperty(wname, cv2.WND_PROP_VISIBLE) < 1:
            break
        cv2.imshow(wname, frame)
        key = cv2.waitKey(2)
        #print(key)
        if key == -1:
            pass
        elif key == 13: #ENTER
            if fileName == '':
                saveFileName = os.path.join(dirPath, 'pic_%04d.png' % (n,))
                cv2.imwrite(saveFileName, frame)
                n += 1
            else:
                saveFileName = os.path.join(dirPath, fileName)
                cv2.imwrite(saveFileName, frame)
                break
            print('save: ', saveFileName)

        elif key == ord('r'):
            if not recordFlag:
                name = 'output_%d.mp4' % fnIdx
                while os.path.isfile(name):
                    fnIdx += 1
                    name = 'output_%d.mp4' % fnIdx
                
                print('recording', name)
                videoWriter = cv2.VideoWriter(
                     name,
                     cv2.VideoWriter_fourcc(*'mp4v'),  # 编码器
                     30,
                     (1920, 1080)
                )
                recordFlag = True

        elif key == ord('f'):
            if recordFlag:
                videoWriter.release()
                print('finish', name)
                recordFlag = False
        
        elif key == 27 or key == ord('q'): #ESC
            break
        goon, frame = cap.read()
        t1 = time.time()
        dt += (t1 - t0 - dt) * 0.1
        t0 = t1
        #print(frame.shape, '  FPS = %f' % (1.0/dt), end='\r')
    cap.release()
    if recordFlag:
        videoWriter.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        dev = int(sys.argv[1])
    else:
        dev = 1
    TakePictures(dev)
    
    
    
    
    
    
    
    
    
