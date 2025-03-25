import wx
from audiolooper import AudioLooper
from looperframe import LooperFrame

def main():
    looper = AudioLooper(initial_loop_lengths=[2.0, 4.0, 8.0])
    try:
        looper.start()
        app = wx.App(False)
        frame = LooperFrame(looper)
        frame.Show()
        app.MainLoop()
    finally:
        looper.stop()
        import time
        time.sleep(0.1)  # Ensure clean exit

if __name__ == "__main__":
    main()