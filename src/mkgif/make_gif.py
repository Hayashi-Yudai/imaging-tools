import matplotlib.pyplot as plt
import matplotlib.animation as animation
from PIL import Image
from glob import glob

if __name__ == "__main__":
    fig = plt.figure(figsize=(14, 14))
    plt.tick_params(labelleft=False, labelbottom=False, left=False, bottom=False)
    plt.gca().spines["right"].set_visible(False)
    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["left"].set_visible(False)
    plt.gca().spines["bottom"].set_visible(False)
    images = []

    img_list = glob("./images/*.png")
    # img_list.sort(key=lambda x: -float(x.rsplit("/", 1)[1].rsplit(".", 1)[0]))

    for img in img_list:
        im = Image.open(img)
        images.append([plt.imshow(im)])

    plt.tight_layout()
    ani = animation.ArtistAnimation(fig, images, interval=500)
    ani.save("simulation.gif")
