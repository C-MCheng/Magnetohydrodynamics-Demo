import h5py
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import os, shutil, sys, time

path = "./data/"
if not os.path.exists(path):
    os.makedirs(path)

def InitializeData(CFL = 0.5, evolutionTime = 0.0, n = 64, nG = 2, L = 1.0, gamma = 5.0/3.0):
    N = n+2*nG
    dL = L/n

    density = np.zeros((N, N, N))
    velocityX = np.zeros((N, N, N))
    velocityY = np.zeros((N, N, N))
    velocityZ = np.zeros((N, N, N))
    thermalPressure = np.zeros((N, N, N))
    l = np.linspace(-dL*(2*nG-1)/2, L+dL*(2*nG-1)/2, N)
    r = np.zeros((N, N, N))
    for yi in range(N):
        for xi in range(N):
            r[:, yi, xi] = np.sqrt(((l-0.5)[xi])**2+((l-0.5)[yi])**2)

    magneticFieldX = np.zeros((N, N, N+1))
    magneticFieldY = np.zeros((N, N+1, N))
    magneticFieldZ = np.zeros((N+1, N, N))

    r0 = 0.1
    r1 = 0.115
    u0 = 2
    def f(r):
        return (r1-r)/(r1-r0)

    density[:] = np.where(r < r0, 10, np.where(r <= r1, 1 + 9 * f(r), 1))
    for yi in range(N):
        for xi in range(N):
            velocityX[:, yi, xi] = np.where(r[:, yi, xi] < r0, u0/r0*(0.5-l[yi]), np.where(r[:, yi, xi] <= r1, f(r[:, yi, xi])*u0/r0*(0.5-l[yi]), 0))
    for yi in range(N):
        for xi in range(N):
            velocityY[:, yi, xi] = np.where(r[:, yi, xi] < r0, u0/r0*(l[xi]-0.5), np.where(r[:, yi, xi] <= r1, f(r[:, yi, xi])*u0/r0*(l[xi]-0.5), 0))
    velocityZ[:,:,:] = 0.0
    thermalPressure[:,:,:] = 1.0
    magneticFieldX[:,:,:] = 5/np.sqrt(4*np.pi)
    magneticFieldY[:,:,:] = 0.0
    magneticFieldZ[:,:,:] = 0.0

    meanMagneticFieldX = np.zeros((N, N, N))
    meanMagneticFieldY = np.zeros((N, N, N))
    meanMagneticFieldZ = np.zeros((N, N, N))
    for zi in range(N):
        for yi in range(N):
            for xi in range(N):
                meanMagneticFieldX[zi, yi, xi] = (magneticFieldX[zi, yi, xi]+magneticFieldX[zi, yi, xi+1])/2
                meanMagneticFieldY[zi, yi, xi] = (magneticFieldY[zi, yi, xi]+magneticFieldY[zi, yi+1, xi])/2
                meanMagneticFieldZ[zi, yi, xi] = (magneticFieldZ[zi, yi, xi]+magneticFieldZ[zi+1, yi, xi])/2

    f = h5py.File(path+"0.h5", "w")
    f.create_group("Parameters")
    f["Parameters"]["CFL"] = np.array([CFL], dtype=np.double) 
    f["Parameters"]["evolutionTime"] = np.array([evolutionTime], dtype=np.double) 
    f["Parameters"]["numberOfCells"] = np.array([n], dtype=np.int32) 
    f["Parameters"]["numberOfGhostCells"] = np.array([nG], dtype=np.int32) 
    f["Parameters"]["domainLength"] = np.array([L], dtype=np.double) 
    f["Parameters"]["heatCapacityRatio"] = np.array([gamma], dtype=np.double) 
    f.create_group("Variables")
    f["Variables"]["density"] = np.double(density.flatten()) 
    f["Variables"]["velocityX"] = np.double(velocityX.flatten()) 
    f["Variables"]["velocityY"] = np.double(velocityY.flatten())
    f["Variables"]["velocityZ"] = np.double(velocityZ.flatten()) 
    f["Variables"]["thermalPressure"] = np.double(thermalPressure.flatten()) 
    f["Variables"]["staggeredMagneticFieldX"] = np.double(magneticFieldX.flatten())
    f["Variables"]["staggeredMagneticFieldY"] = np.double(magneticFieldY.flatten()) 
    f["Variables"]["staggeredMagneticFieldZ"] = np.double(magneticFieldZ.flatten()) 
    f["Variables"]["magneticFieldX"] = np.double(meanMagneticFieldX.flatten())
    f["Variables"]["magneticFieldY"] = np.double(meanMagneticFieldY.flatten())
    f["Variables"]["magneticFieldZ"] = np.double(meanMagneticFieldZ.flatten())
    f.close()

def DrawData(path = path):
    def sortInteger(fileName):
        try:
            baseName = os.path.splitext(fileName)[0] 
            return int(baseName)
        except (ValueError, IndexError): 
            return 

    fileList = [file for file in os.listdir(path) if file.endswith(".h5")]
    sortedFileList = sorted(fileList, key=sortInteger)

    for file in sortedFileList: 
        f = h5py.File(path+file, "r")
        n = f["Parameters"]["numberOfCells"][()] 
        n = n[0] 
        nG = f["Parameters"]["numberOfGhostCells"][()] 
        nG = nG[0] 
        L = f["Parameters"]["domainLength"][()] 
        L = L[0] 
        rho = f["Variables"]["density"][()]
        vx = f["Variables"]["velocityX"][()]
        vy = f["Variables"]["velocityY"][()]
        vz = f["Variables"]["velocityZ"][()] 
        p = f["Variables"]["thermalPressure"][()] 
        Bx = f["Variables"]["magneticFieldX"][()] 
        By = f["Variables"]["magneticFieldY"][()] 
        Bz = f["Variables"]["magneticFieldZ"][()] 
        f.close()

        N = n+2*nG
        dL = L/n 
        l = np.linspace(-dL*(2*nG-1)/2, L+dL*(2*nG-1)/2, N) 

        rho = np.reshape(rho, (N , N, -1))
        vx = np.reshape(vx, (N , N, -1))
        vy = np.reshape(vy, (N , N, -1))
        vz = np.reshape(vz, (N , N, -1))
        p = np.reshape(p, (N , N, -1))
        Bx = np.reshape(Bx, (N , N, -1))
        By = np.reshape(By, (N , N, -1))
        Bz = np.reshape(Bz, (N , N, -1))
        
        figProfile, axes = plt.subplots(1, 2, figsize=(14, 6))
        axes = axes.flatten() 
        cbar_list = [None] * len(axes)
        figProfile.subplots_adjust(
            left=0.02,    
            right=0.9,   
            bottom=0.1,  
            top=0.9,     
            wspace=0.1,   
        )
        """
        rho = rho[N//2, nG:-nG, nG:-nG]
        vx = vx[N//2, nG:-nG, nG:-nG]
        vy = vy[N//2, nG:-nG, nG:-nG]
        vz = vz[N//2, nG:-nG, nG:-nG]
        p = p[N//2, nG:-nG, nG:-nG]
        Bx = Bx[N//2, nG:-nG, nG:-nG]
        By = By[N//2, nG:-nG, nG:-nG]
        l = l[nG:-nG] 
        """
        rho = rho[N//2]
        vx = vx[N//2]
        vy = vy[N//2]
        vz = vz[N//2]
        p = p[N//2]
        Bx = Bx[N//2]
        By = By[N//2]
        
        variables = [rho, p]
        variablesName = ["Density", "Pressure"]
        plt.suptitle("MHD Rotor (nx=ny=nz="+str(n)+") at Time: 0.15", fontsize=14)
        for j, ax in enumerate(axes):
            ax.clear()
            mesh = ax.imshow(variables[j], extent=[l[0], l[-1], l[0], l[-1]], origin="lower", interpolation='bilinear', cmap='inferno') 
            ax.set_aspect('equal', adjustable='box')
            cbar = figProfile.colorbar(mesh, ax=ax, fraction=0.0457, pad=0.04, label=variablesName[j])
            cbar_list[j] = cbar
            skip = 4 
            ax.quiver(l[::skip], l[::skip], Bx[::skip, ::skip], By[::skip, ::skip], color='lightsteelblue')
        plt.savefig(path+"fig"+file+".png")
        plt.close()
        figProfile.clf() 
   
#InitializeData()
#DrawData()