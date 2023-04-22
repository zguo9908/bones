import time
from krave import utils
import tkinter
from PIL import Image, ImageTk
import os


class Visual_tk():

    def __init__(self, mouse,exp_config):
        # find_monitor()
        # super().__init__()
        self.mouse = mouse
        self.exp_config = exp_config
        self.hardware_config_name = self.exp_config['hardware_setup']
        self.hardware_config = utils.get_config('krave.hardware', 'hardware.json')[self.hardware_config_name]

        self.cue_name = self.exp_config['visual_cue_name']
        self.cue_path = utils.get_path('krave.hardware', f'visual_cue_img/{self.cue_name}')
        self.cue_duration = self.exp_config['visual_display_duration']
        self.cue_location = tuple(self.exp_config['visual_cue_location'])
        self.image_on_canvas = None
        self.image_change_count = 0

        self.screen = None
        self.screen_ready = False
        self.cue = None
        self.cue_displaying = False
        self.cue_on_time = None

        self.find_monitor()

        # create tkinter object
        self.root = tkinter.Tk()
        self.w, self.h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.overrideredirect(1)
        self.root.geometry("%dx%d+0+0" % (self.w, self.h))
        self.root.focus_set()
        self.root.bind("<Escape>", lambda e: (e.widget.withdraw(), e.widget.quit()))

        # create canvas that has the size of my screen
        self.screen = tkinter.Canvas(self.root, width=self.w, height=self.h)
        self.screen.pack()
        self.screen.configure(background='black')

        self.screen_on = True



    def find_monitor(self):
        if os.environ.get('DISPLAY', '') == '':
            print('no display found. Using :0.0')
            os.environ.__setitem__('DISPLAY', ':0.0')
        self.screen_ready = True

    # create correctly sized tkinter image from PIL image
    def create_image(self,pilImage):
        # get size of the image and resize it to the canvas
        imgWidth, imgHeight = pilImage.size
        if imgWidth > self.w or imgHeight > self.h:
            ratio = min(self.w / imgWidth, self.h / imgHeight)
            imgWidth = int(imgWidth * ratio)
            imgHeight = int(imgHeight * ratio)
            pilImage = pilImage.resize((imgWidth, imgHeight), Image.ANTIALIAS)
        image = ImageTk.PhotoImage(pilImage)
        return image

    # tkinter visual control with the after() method.
    # should modify to take inputs of the experimental times
    def visual_control_with_after(self):
        # create cues
        cue_on = self.create_image(Image.open(self.cue_path))
        cue_off = self.create_image(Image.new(mode="RGBA", size=(1920, 1080)))

        # update image
        def update_canvas():
            self.image_change_count += 1
            # print("updating")
            if self.image_change_count % 2 != 0:
                # print(self.image_change_count)
                print("update to black screen")
                print(time.time())
                self.screen.itemconfig(on_screen, image=cue_off)
                self.cue_displaying = False
                self.screen.update()
            else:
                print("update to cue")
                print(time.time())
                self.screen.itemconfig(on_screen, image=cue_on)
                self.cue_displaying = True
                self.screen.update()

            self.root.after(5000, update_canvas)
            print("updated")


        # update_canvas
        self.root.after(5000, update_canvas)

        # put cue on canvas
        on_screen = self.screen.create_image(self.w/2, self.h/2, image=cue_on)
        self.cue_on_time = time.time()
        print(self.cue_on_time)
        self.cue_displaying = True
        # cue_off_screen = self.screen.create_image(self.w/2, self.h/2, image=cue_off)
        self.root.mainloop()


    def shutdown(self):
        self.root.destroy()
        self.screen_on = False
        self.cue_displaying = False



    def visual_control(self, full_screen):
        self.find_monitor()

        root = tkinter.Tk()
        w, h = root.winfo_screenwidth(), root.winfo_screenheight()
        root.overrideredirect(1)
        root.geometry("%dx%d+0+0" % (w, h))
        root.focus_set()
        root.bind("<Escape>", lambda e: (e.widget.withdraw(), e.widget.quit()))

        # create canvas that has the size of my screen
        canvas = tkinter.Canvas(root, width=w, height=h)
        canvas.pack()
        canvas.configure(background='black')



        # create tkinter compatible photo image
        if full_screen:
            cue_on = self.create_image(Image.open(self.cue_path), w, h)
            cue_off = self.create_image(Image.new(mode="RGBA", size=(1920, 1080)), w,h)
        else:
            cue_on = ImageTk.PhotoImage(Image.open(self.cue_path))
            cue_off = ImageTk.PhotoImage(Image.new(mode="RGBA", size=(1920, 1080)))

        # update image
        def update(image):
            canvas.create_image(w / 2, h / 2, image=cue_off)

        # Create a button to update the canvas image
        button = tkinter.Button(root, text="Update", command=lambda: update())
        button.pack()

        # Add image to the canvas
        image_container = canvas.create_image(0, 0, anchor="nw", image=cue_on)
        root.mainloop()




# deprecated stuff
    #
    # def cue_on(self, loop_on):
    #     self.cue_displaying = True
    #     # if self.loop_on is not None:
    #     #      self.loop_on.quit()
    #     self.cue_on_time = time.time()
    #     self.find_monitor()
    #     print(self.cue_path)
    #     self.cue = Image.open(self.cue_path)
    #     self.loop_on = showPIL(1000,self.cue)
    #     print("cue shown")
    #     return self.cue_on_times
    #
    # def cue_off(self):
    #     self.cue_displaying = False
    #     if self.loop_on is not None:
    #          self.loop_on.quit()
    #     new = Image.new(mode="RGBA", size=(1920, 1080))
    #     self.find_monitor()
    #     self.loop_on = showPIL(new)
    #     return time.time()






    # # get size of the image and resize it to the canvas
    # imgWidth, imgHeight = pilImage.size
    # if imgWidth > w or imgHeight > h:
    #     ratio = min(w / imgWidth, h / imgHeight)
    #     imgWidth = int(imgWidth * ratio)
    #     imgHeight = int(imgHeight * ratio)
    #     pilImage = pilImage.resize((imgWidth, imgHeight), Image.ANTIALIAS)
    #
    # # create tkinter compatible photo image
    # image = ImageTk.PhotoImage(pilImage)
    # imagesprite = canvas.create_image(w / 2, h / 2, image=image)
