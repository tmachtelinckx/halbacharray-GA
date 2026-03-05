import matplotlib.pyplot as plt
import numpy as np
import math
from mpl_toolkits.mplot3d import Axes3D 
#import sys

# Work in mm and use radii

class HallbachRing:
    def __init__(self, magnetSize=12, boreRadius=100, outerBoreRadius=190, magnetRingRadii=[-1]*3, magnetsInRingNr=[-1]*3, bandGap = 0, magnetSpace = 0, bandSep = 0):

        # Primary function of this class is to check that all parameters work,
        # and throw an error should it not be the case.
        # Also show how many magnets can still be added etc.

        # User input to initiate:
        # Magnet Size
        # Bore size
        # Number of rings
        # Initiate array for individual magnet ring radii, magnet numbers of each. (Enter -1 to set to maximum)
        # Outer border is not so NB, but implement regardless

        self.magnetSize = magnetSize
        self.magnetRadius = self.calculateMagnetRadius(magnetSize)
        self.boreRadius = boreRadius
        self.outerBoreRadius = outerBoreRadius
        self.bandGap = bandGap
        self.magnetSpace = magnetSpace
        self.magnetRing = []
        self.bandSep = bandSep

        for index, magnetRingRadius in enumerate(magnetRingRadii):
            self.magnetRing.append(self.createMagnetRing(index, magnetRingRadius, magnetsInRingNr[index], self.bandGap, self.bandSep))

        return None
    
    @classmethod
    def calculateMagnetRadius(self, magnetSize):
        # Note here radii are slightly larger than magnet.
        return math.ceil(np.sqrt(((magnetSize**2)/2)))

    def calculateMaxMagnetNumber(self, magnetRadius, magnetRingRadius, magnetSpace):
        return round(np.pi/np.arcsin((self.magnetRadius + (magnetSpace/2))/magnetRingRadius))

    def calculateMagnetPositions(self, magnetNumber):
        # Returns magnet positions in radius distributed around a circle
        # If you use a max value, it might need to be rounded.
        return np.linspace(0, 2*np.pi, round(magnetNumber), endpoint = False)

    def createMagnetRing(self, index, magnetRingRadius, magnetsInRingNr, bandGap, bandSep):

        # Checks parameters and stores in a array of dictionaries if correct.

        if(index == 0):
            minimumRadius = self.boreRadius + self.magnetRadius + bandSep
        else:
            minimumRadius = self.magnetRing[index -1]['ringRadius']+self.magnetRadius*2 + bandGap

        if(magnetRingRadius == -1):
            magnetRingRadius = minimumRadius

        if(magnetRingRadius < minimumRadius):
            raise ValueError("magnetRing %d: magnetRing magnet radius of %.3fmm is too small. Minimum is %.3f" % (
                index, magnetRingRadius, minimumRadius))

        maxRingMagnetNr = self.calculateMaxMagnetNumber(
            self.magnetRadius, magnetRingRadius, self.magnetSpace)

        if(magnetsInRingNr == -1):

            magnetsInRingNr = maxRingMagnetNr

        elif(magnetsInRingNr > maxRingMagnetNr):
            raise ValueError("magnetRing %d: Can not fit %d magnets in a radius of %.3fmm. Max is %d"
                             % (index, magnetsInRingNr, magnetRingRadius, maxRingMagnetNr))

        #magnetSpacing = np.diff(calculateMagnetPositions(magnetsInRingNr))

        aMagnetRing = {

            "ringRadius": magnetRingRadius,
            "magnetsInRingNr": magnetsInRingNr}

        return aMagnetRing

    def plotSingleRing(self, MagnetNumber, magnetRadius, ringRadius, ax):

        magnetTheta = self.calculateMagnetPositions(MagnetNumber)

        theta = np.arange(0, 2*np.pi, 150)

        for i in magnetTheta:

           # Calculate circle position
            x = ringRadius * np.cos(i)
            y = ringRadius * np.sin(i)

            # Draw the circle (magnet)
            circle1 = plt.Circle((x, y), magnetRadius, color='blue', fill=False)
            ax.add_patch(circle1)

            # Calculate the dimensions of the square inside the circle
            square_side = self.magnetSize
            square_left = x - square_side / 2
            square_bottom = y - square_side / 2

            # Determine the rotation of the square (360 degrees for every 180 degrees around the ring)
            squareAngle = np.degrees(i) * 2

            # Draw the square inside the circle
            square = plt.Rectangle((square_left, square_bottom), square_side, square_side, angle = squareAngle, rotation_point = 'center',  edgecolor='blue', fill=False)
            ax.add_patch(square)

        innerCircle = plt.Circle((np.cos(theta), np.sin(
            theta)), ringRadius, color='black', linestyle='--', fill=False)
        ax.add_patch(innerCircle)


        return ax

    def drawHallbach(self,fileName=""):

        fig, ax = plt.subplots()
        #plt.grid()

            # **Force limits to exactly outerBoreRadius**
        ax.set_xlim([-self.outerBoreRadius*1.3, self.outerBoreRadius*1.3])
        ax.set_ylim([-self.outerBoreRadius*1.3, self.outerBoreRadius*1.3])

            # Force equal aspect ratio so circle is round
        ax.set_aspect('equal', 'box')
        #outerCircle = plt.Circle((0,0), self.OuterRadius, color='black',fill=False)
        # ax.add_patch(outerCircle)

        boreCircle = plt.Circle((0, 0), self.boreRadius,
                                color='black', fill=False)
        ax.add_patch(boreCircle)

        for i in range(len(self.magnetRing)):
            #RingBorder = plt.Circle(
            #    (0, 0), self.magnetRing[i]['ringRadius']+self.magnetRadius, color='gray', linestyle='--', fill=False)
            #ax.add_patch(RingBorder)
            ax = self.plotSingleRing(
                self.magnetRing[i]['magnetsInRingNr'], self.magnetRadius, self.magnetRing[i]['ringRadius'], ax)
        
        outerCircle = plt.Circle((0, 0), self.outerBoreRadius, color='black', fill=False)
        ax.add_patch(outerCircle)

        if (fileName != ""):
            plt.savefig(fileName)
            plt.close()
            print("Wrote %s" %(fileName))    
        else:
            plt.show()

        return ax


    def getParameters(self):

        ringRadii = np.empty(len(self.magnetRing))
        magnetsInRingNrs = np.empty(len(self.magnetRing))

        for i in range(len(self.magnetRing)):
            ringRadii[i] = self.magnetRing[i]['ringRadius']
            magnetsInRingNrs[i] = self.magnetRing[i]['magnetsInRingNr']

        return ringRadii, magnetsInRingNrs
    
    def drawStackedRings(self, num_rings=6, spacing=25):


        ringRadii, magnetsInRingNrs = self.getParameters()

        # Let's pick the outermost ring to stack (last ring)
        radius = ringRadii[-1]
        num_magnets = int(magnetsInRingNrs[-1])

    # Calculate magnet angles
        magnet_angles = self.calculateMagnetPositions(num_magnets)

    # Calculate x,y positions for magnets on a single ring
        x = radius * np.cos(magnet_angles)
        y = radius * np.sin(magnet_angles)

    # Create 3D plot
        fig = plt.figure(figsize=(8,6))
        ax = fig.add_subplot(111, projection='3d')

    # Plot stacked rings along z-axis
        for i in range(num_rings):
            z = np.full_like(x, i * spacing)  # Z coordinate for this ring
            ax.scatter(x, y, z, label=f'Ring {i+1}', s=50)

    # Plot bore and outermost ring as circles in XY plane at z=0 and at top and bottom for visualization
    # For visualization, draw bore and outer circle as wireframe rings along z axis range
        z_range = np.linspace(0, (num_rings - 1) * spacing, 100)
        bore_radius = self.boreRadius
        bore_x = bore_radius * np.cos(np.linspace(0, 2*np.pi, 100))
        bore_y = bore_radius * np.sin(np.linspace(0, 2*np.pi, 100))
        outer_x = (radius + self.magnetRadius) * np.cos(np.linspace(0, 2*np.pi, 100))
        outer_y = (radius + self.magnetRadius) * np.sin(np.linspace(0, 2*np.pi, 100))

    # Plot bore cylinder (wireframe)
        for zc in z_range[::10]:
            ax.plot(bore_x, bore_y, zs=zc, zdir='z', color='black', alpha=0.2, linestyle='--')

    # Plot outer cylinder (wireframe)
        for zc in z_range[::10]:
            ax.plot(outer_x, outer_y, zs=zc, zdir='z', color='gray', alpha=0.2, linestyle='--')

        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_zlabel('Z (mm)')
        ax.set_title(f'Stacked {num_rings} Halbach Rings with spacing {spacing} mm')

        ax.legend()
        ax.grid(True)

    # Equal aspect ratio in 3D is tricky, but we can set limits
        # Compute limits including outer bore
        # Compute max radius including outer bore and outermost ring
        outermost_radius = max(self.outerBoreRadius, radius + self.magnetRadius)
        margin = 1.1  # 10% margin
        ax.set_xlim([-outermost_radius*margin, outermost_radius*margin])
        ax.set_ylim([-outermost_radius*margin, outermost_radius*margin])
        plt.show()