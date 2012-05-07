#! /usr/bin/env python
# -*- coding: UTF-8 -*- 

###########################################################################
#            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#                    Version 2, December 2004
#
# Copyright 2012 - gcoop - Cooperativa de Software Libre
# http://gcoop.coop
# Everyone is permitted to copy and distribute verbatim or modified
# copies of this license document, and changing it is allowed as long
# as the name is changed.
#
#            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION
#
#
#  0. You just DO WHAT THE FUCK YOU WANT TO. 
###########################################################################


import subprocess
import pynotify
import os
import socket
import fcntl
import struct

# Los 2 rangos de IP en los cuales estoy todos los dias, y en función de ellos donde hacer el backup
config={'192.168.10':'jose@malbec:/bacoop/jose', '192.168.0':'jose@reylagarto:/home/jose/backup_notebook/'}

# Directorios a excluir con rsync
exclude =('gcoop/*', '.ssh/*', '.gvfs/*', '.thunderbird/*/ImapMail/*', '.mozilla/firefox/*/Cache/*', '.thunderbird/*/Cache/*', '.macromedia/*', '.thunderbird/*/global-messages-db.sqlite-journal', '.local/share/Trash/*')

# Mail a donde mandarme los errores al hacer backup
direccion_mail = 'yo@midominio'

home = '/home/jose/'



# Clase para crear y destruir un archivo lock que impide ejecutar el script si ya está en proceso.
class TmpFile(object):
    def __init__(self,name='/tmp/backup_notebook.lock'):
        self.name = name


    def create(self):
    	try:
            tmp = open(self.name,'r')
            print "#"*80,"\n  El script está siendo ejecutado \n", "#"*80
	    sys.exit(1)
            raise SystemExit # el sys.exit no salia :|
        except:
            tmp = open(self.name,'w')
            tmp.write('$$$.lock.$$$')
            tmp.close()

    def destroy(self):
    	if os.path.isfile( self.name ):
            os.unlink( self.name )


# Clase que, básicamente, hace el backup :P
class Backup (object):

    def __init__(self, excludefile='/tmp/excludefile'):
        self.obtener_ip()
        self.direccion_mail = direccion_mail
        self.excludefile=excludefile
        self.creararchivo()

    def aviso(self, estado, donde, msg = ''):
            if estado == 'start':
                aviso_inicio = pynotify.init('backup')
                aviso_inicio = pynotify.Notification("Comenzando Backup!", message="En "+donde, icon='document-save-as')
                aviso_inicio.show()
            elif estado == 'stop':
                aviso_fin = pynotify.init('backup')
                aviso_fin = pynotify.Notification("Finalizando Backup!", message="En "+donde, icon='document-save')
                aviso_fin.show()
            elif estado == 'error':
                aviso_error = pynotify.init('backup')
                aviso_error = pynotify.Notification("Error en Backup!", message="Error al realizar backup en "+donde+". "+msg, icon='stop')
                aviso_error.show()            

    def buscar_host(self):
        
        for i in config.keys():
             if self.ip.startswith(i):
                 return config[i]

    def creararchivo(self):
        archivo = open(self.excludefile,'w')
        
        for e in exclude:
            archivo = open(self.excludefile,'a')
            archivo.write(e+'\n')
            archivo.close()

    def notificar_error(self, error, donde):
            host = self.buscar_host()
            mail = 'echo "Error al hacer backup en '+donde+ '\n\n'+error+'" | mail -s "Error al hacer backup en '+donde+'" -t "'+self.direccion_mail+'"'
            mandomail = subprocess.Popen(mail, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
            self.aviso('error', host)        

        
    def obtener_ip(self, ifname='eth0'):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ip = socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])

    def hacer_backup(self):
        host = self.buscar_host()
        if host:
            print host

            if(host.find('malbec') != -1):
                ssh = subprocess.Popen('ssh malbec "ls -l /bacoop/jose | grep -v total | wc -l"',  shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                total = int(ssh.stdout.readline())


                if (total > 0 and host.find('malbec')):
                    self.aviso('start', host)
                    rsync = 'rsync -e ssh -avz --exclude-from='+self.excludefile+' '+home+' '+host
                    print rsync
                    mando = subprocess.Popen(rsync, shell=True, stderr=subprocess.PIPE )
                   
                    if (mando.wait() != 0):
                        self.notificar_error(mando.stderr.read(), host)
                        self.aviso('stop', host)
                    else:
                        self.aviso('stop', host)

                else:
                    self.aviso('error', host, 'No está montado /bacoop/jose/')
                    self.notificar_error('No está montado /bacoop/jose/', host)
                    
            else:
                self.aviso('start', host)
                rsync = 'rsync -e ssh -avz --exclude-from='+self.excludefile+' '+home+' '+host
                print rsync
                mando = subprocess.Popen(rsync, shell=True, stderr=subprocess.PIPE )

                if (mando.wait() != 0):
                    self.notificar_error(mando.stderr.read(), host)
                    self.aviso('stop', host)

        else:
            print 'No reconocí host'
                   

## Inicio del Script.
t = TmpFile() # creo un archivo temporal en /tmp
t.create()    # si este existe, salgo inmediatamente, sino creo uno

b = Backup()
b.hacer_backup()

t.destroy()
