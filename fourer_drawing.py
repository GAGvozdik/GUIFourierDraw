import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

poitnsL = 56


phis = np.linspace(0, 2*np.pi, poitnsL + 1)[:-1]

res = np.empty(poitnsL)
for i in range(poitnsL):
    if phis[i] < np.pi/4:
        res[i] = 200.0
    elif np.pi/4 <= phis[i] < 3*np.pi/4:
        res[i] = 200/np.tan(phis[i])
    elif 3*np.pi/4 <= phis[i] < 5*np.pi/4:
        res[i] = -200.0
    elif 5*np.pi/4 <= phis[i] < 7*np.pi/4:
        res[i] = -200/np.tan(phis[i])
    else:
        res[i] = 200.0

ims = np.empty(poitnsL)
for i in range(poitnsL):
    if phis[i] < np.pi/4:
        ims[i] = np.tan(phis[i])
    elif np.pi/4 <= phis[i] < 3*np.pi/4:
        ims[i] = 1.0
    elif 3*np.pi/4 <= phis[i] < 5*np.pi/4:
        ims[i] = -np.tan(phis[i])
    elif 5*np.pi/4 <= phis[i] < 7*np.pi/4:
        ims[i] = -1.0
    else:
        ims[i] = np.tan(phis[i])

def cn(n, res, ims):
    exparr = np.exp(-1j*n*phis)
    return (np.dot(exparr, res) + 1j*np.dot(exparr, ims)) * 0.0001

cns = np.array([cn(i, res, ims) for i in range(-100,101)])

# plt.scatter(np.arange(-10, 11), cns[90:111].real)
# plt.scatter(np.arange(-10, 11), cns[90:111].imag)
# print('i\tc')
# for i, c in zip(np.arange(-10, 11), cns[90:111]):
#     print(i, c, sep='\t')
# plt.show()


test = np.sum(np.array(
    [cns[i+100] * np.exp(-1j*i*phis) for i in range(-100,101)]), axis=0)

fig = plt.figure(figsize=(6.4, 6.4))
images = []
plt.axis('off')
plt.plot(np.real(test), np.imag(test), c='grey', linewidth='1.0')

for phi in np.linspace(0, 2*np.pi, 1001)[:-1]:
    arrows = np.zeros((201,2))
    z = cns[100]
    arrows[0] = z.real, z.imag
    for i in range(1, 100):
        z = cns[100+i] * np.exp(1j*i*phi)
        arrows[2*i-1] = z.real, z.imag
        z = cns[100-i] * np.exp(-1j*i*phi)
        arrows[2*i] = z.real, z.imag
    sums = np.zeros_like(arrows)
    sums[0] = arrows[0]
    for i in range(1,201):
        sums[i] = sums[i-1] + arrows[i]
    image, = plt.plot(sums[:,0], sums[:,1], c='black', linewidth='1.0', animated=True)
    images.append([image])

ani = animation.ArtistAnimation(fig, images, interval=20, blit=True, repeat_delay=20)

plt.show()