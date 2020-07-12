# -*- coding: iso-8859-1 -*-

# From  Michael Rugel and the THOR project.

import glob
import os

def breathe(resttime=3):
		mylogfile = casalog.logfile()
		countmax = 100
		countr = 0
		foundend=False
		while not foundend and countr<countmax:
				os.system('sleep '+str(resttime)+'s')
				#os.system('tail --lines=30 '+mylogfile)
				f = os.popen('tail --lines=30 '+mylogfile)
				fstrs = f.readlines()
				f.close()
				for fstr in fstrs:
						if fstr.count('End Task: plotms')>0:
								foundend=True
								print 'Found end of task plotms in logfile at count '+str(countr)
				countr+=1
				crash = True
				for fstr in fstrs:
						if fstr.count('Generating the plot mask')>0:
								crash = False
				if crash == True:
						print 'plotms crashed'
						break
				else:
						print 'plotms works, sleeping...'
						os.system('sleep '+str(resttime)+'s')


def make_plots(ms_active,caltabledir='./',plotdir='./quality_images/',spw_id=[0],field_flux1 = '0',field_flux2 = None, field_gain1 ='1',field_gain2 =None, plot_dic = None, wlogfile=False):
	"""
	ms_active   : Name of the ms (including path)
	caltabledir='./final_caltables/' : Directory in which caltables are stored
	plotdir='./quality_images/' : Directory in which plots should be stored
	spw_id=[0]  : List of spws to be plotted, e.g., [0,1,2]
	field_flux1='0'  : Field ID of the flux calibrator
	field_flux2=None : Field ID of second flux calibrator (needed for some GLOSTAR obs)
	field_gain1='1'  : Field ID of the gain calibrator
	field_gain2=None : Field ID of second gain calibrator (needed for some THOR GC obs)
	plot_dic  =None  : dictionary of spws to be plotted together for gain solutions
					   (amp/phase vs. time) (default: plot all spws separately). If CONT is in list, then also these bandpasses will be plotted together.
	wlog=False       : log the commands into the html log

	Example for plot_dic:
	plot_dic = {
	'CONT': '0,2,16,17,18,20,26,30',
	'HI': '12',
	'OH': '20,22,24',
	'RRL_A0C0': '1,3,4,5,6,7,8,9,10,11,13,14,15', #rrls in baseband A0C0
	'RRL_B0D0': '21,23,25,27,28,29', #rrls in baseband B0D0
	}

	"""
	#---------------------------------------
	#Preparations
	#---------------------------------------
	# get absolute paths
	caltabledir = os.path.abspath(caltabledir)
	plotdir = os.path.abspath(plotdir)

	# create plotdir
	try:
		os.makedirs(plotdir)
	except:
		pass

	# create weblog
	if not wlogfile:
		wlogfile = os.path.join(plotdir,'weblog.html')
	wlog = open(wlogfile,"w")
	wlog.write('<html>\n')
	wlog.write('<head>\n')
	wlog.write('<title>Quality assurance plots</title>\n')
	wlog.write('</head>\n')
	wlog.write('<body>\n')
	wlog.write('<br>\n')
	wlog.write('<hr>\n')
	wlog.close()

	# get number of antenna
	nantenna = 27
	nplots   = int(np.ceil(nantenna/3.))

	try:
		## define bandpass id strings:
		bp_id = {}
		for i in spw_id:
			bp_id[str(i)] = str(i)

		if plot_dic:
			if np.in1d(['CONT'],plot_dic.keys())[0]:
				spw_cont = plot_dic['CONT'].split(',')
				bp_id['CONT'] = plot_dic['CONT']
				print spw_cont
				for i in spw_cont:
					del bp_id[i]

		## define gain solution ID strings :
		if plot_dic:
			gain_id = plot_dic
		else:
			gain_id = {}
			for i in spw_id:
				gain_id[str(i)] = str(i)

		#---------------------------------------
		#Plot flux calibrator 1  Real vs Imag:
		#---------------------------------------
		wlog = open(wlogfile,"a+")
		wlog.write('<h1>Plot Flux calibrator 1 Real vs Imag: </h1> \n')
		for ii in spw_id:
			name = os.path.join(plotdir,'flux_calibrator1_spw'+str(ii)+'_Real-Imag.png')
			print name
			file_exist = os.path.isfile(name) or os.path.isfile('weblog/'+name)
			if file_exist == True:
				print 'Plot '+name+' already exists.'
			else:
				print ii
				plotms(vis=ms_active,xaxis='real',yaxis='imag',xdatacolumn='corrected',ydatacolumn='corrected',selectdata=True,field=field_flux1,spw=str(ii),scan='',correlation='RR,LL',averagedata=True,avgscan=False,transform=False,avgchannel='10000',extendflag=False,iteraxis='',coloraxis='antenna1',plotrange=[],title='Flux Calibrator 1 - Spw '+str(ii),xlabel='Real',ylabel='Imag',showmajorgrid=True,showminorgrid=True,plotfile=name,overwrite=True,showgui=False)
				breathe()
				if wlog:
						# include image in weblog
						wlog.write('<br><img src="'+name.split('/')[-1]+'"n')
						# include command in weblog
						last = open('plotms.last', 'r')
						for line in last:
							pass
						wlog.write('<br>'+line[1:].split(',plotfile')[0]+')'+' \n')
						wlog.write('<br>\n')
						wlog.write('<br>\n')
						wlog.write('<hr>\n')
		breathe(resttime = 10)
		os.system('rm -rf *_3')
		wlog.close()
		#---------------------------------------
		#Plot flux calibrator 2  Real vs Imag:
		#---------------------------------------
		wlog = open(wlogfile,"a+")
		if field_flux2:
			wlog.write('<h1>Plot Flux calibrator 2 Real vs Imag: </h1> \n')
			for ii in spw_id:
				name = os.path.join(plotdir,'flux_calibrator2_spw'+str(ii)+'_Real-Imag.png')
				print name
				file_exist = os.path.isfile(name) or os.path.isfile('weblog/'+name)
				if file_exist == True:
					print 'Plot '+name+' already exists.'
				else:
					print ii
					plotms(vis=ms_active,xaxis='real',yaxis='imag',xdatacolumn='corrected',ydatacolumn='corrected',selectdata=True,field=field_flux2,spw=str(ii),scan='',correlation='RR,LL',averagedata=True,avgscan=False,avgchannel='10000',transform=False,extendflag=False,iteraxis='',coloraxis='antenna1',plotrange=[],title='Flux Calibrator 2 - Spw '+str(ii),xlabel='Real',ylabel='Imag',showmajorgrid=True,showminorgrid=True,plotfile=name,overwrite=True,showgui=False)
					breathe()
					if wlog:
							# include image in weblog
							wlog.write('<br><img src="'+name.split('/')[-1]+'"n')
							# include command in weblog
							last = open('plotms.last', 'r')
							for line in last:
								pass
							wlog.write('<br>'+line[1:].split(',plotfile')[0]+')'+' \n')
							wlog.write('<br>\n')
							wlog.write('<br>\n')
							wlog.write('<hr>\n')
			breathe(resttime = 10)
			os.system('rm -rf *_3')
		wlog.close()
		#---------------------------------------
		#Plot gain calibrator 1 Real vs Imag:
		#---------------------------------------
		wlog = open(wlogfile,"a+")
		wlog.write('<h1>Plot gain calibrator 1 Real vs Imag: </h1> \n')
		for ii in spw_id:
			name = os.path.join(plotdir,'gain_calibrator1_spw'+str(ii)+'_Real-Imag.png')
			file_exist = os.path.isfile(name) or os.path.isfile('weblog/'+name)
			if file_exist == True:
				print 'Plot '+name+' already exists.'
			else:
				print ii
				plotms(vis=ms_active,xaxis='real',yaxis='imag',xdatacolumn='corrected',ydatacolumn='corrected',selectdata=True,field=field_gain1,spw=str(ii),scan='',correlation='RR,LL',averagedata=True,avgscan=False,avgchannel='10000',transform=False,extendflag=False,iteraxis='',coloraxis='antenna1',plotrange=[],title='Gain Calibrator 1 - Spw '+str(ii),xlabel='Real',ylabel='Imag',showmajorgrid=True,showminorgrid=True,plotfile=name,overwrite=True,showgui=False)
				breathe()
				if wlog:
					# include image in weblog
					wlog.write('<br><img src="'+name.split('/')[-1]+'"n')
					# include command in weblog
					last = open('plotms.last', 'r')
					for line in last:
						pass
					wlog.write('<br>'+line[1:].split(',plotfile')[0]+')'+' \n')
					wlog.write('<br>\n')
					wlog.write('<br>\n')
					wlog.write('<hr>\n')
		breathe(resttime = 10)
		os.system('rm -rf *_3')
		wlog.close()

		#---------------------------------------
		#Plot gain calibrator 2 Real vs Imag:
		#---------------------------------------
		wlog = open(wlogfile,"a+")
		if field_gain2:
			wlog.write('<h1>Plot gain calibrator 2 Real vs Imag: </h1> \n')
			for ii in spw_id:
				name = os.path.join(plotdir,'gain_calibrator2_spw'+str(ii)+'_Real-Imag.png')
				file_exist = os.path.isfile(name) or os.path.isfile('weblog/'+name)
				if file_exist == True:
					print 'Plot '+name+' already exists.'
				else:
					print ii
					plotms(vis=ms_active,xaxis='real',yaxis='imag',xdatacolumn='corrected',ydatacolumn='corrected',selectdata=True,field=field_gain2,spw=str(ii),scan='',correlation='RR,LL',averagedata=True,avgscan=False,avgchannel='10000',transform=False,extendflag=False,iteraxis='',coloraxis='antenna1',plotrange=[],title='Gain Calibrator 2 - Spw '+str(ii),xlabel='Real',ylabel='Imag',showmajorgrid=True,showminorgrid=True,plotfile=name,overwrite=True,showgui=False)
					breathe()
					if wlog:
							# include image in weblog
							wlog.write('<br><img src="'+name.split('/')[-1]+'"n')
							# include command in weblog
							last = open('plotms.last', 'r')
							for line in last:
									pass
							wlog.write('<br>'+line[1:].split(',plotfile')[0]+')'+' \n')
							wlog.write('<br>\n')
							wlog.write('<br>\n')
							wlog.write('<hr>\n')
			breathe(resttime = 10)
			os.system('rm -rf *_3')
		wlog.close()

		#---------------------------------------
		#Check RFI of FLUXCAL1:
		#---------------------------------------
		wlog = open(wlogfile,"a+")
		wlog.write('<h1>Plot flux calibrator 1 Amp vs Channel: </h1> \n')
		for ii in spw_id:
				name = os.path.join(plotdir,'flux_calibrator1_spw-'+str(ii)+'_channel-amp_after_calibration.png')
				file_exist = os.path.isfile(name) or os.path.isfile('weblog/'+name)
				if file_exist == True:
					print 'Plot '+name+' already exists.'
				else:
					print ii
					plotms(vis=ms_active,xaxis='channel',yaxis='amp',ydatacolumn='corrected',selectdata=True,field=field_flux1,spw=str(ii),scan='',correlation='RR,LL',averagedata=True,avgscan=False,transform=False,extendflag=False,iteraxis='',coloraxis='antenna1',plotrange=[],title='Flux Calibrator 1 Spw - '+str(ii)+' - channel vs. amp - after calibration ',xlabel='Channel',ylabel='Amplitude',showmajorgrid=True,showminorgrid=True,plotfile=name,overwrite=True,showgui=False)
					breathe()
					if wlog:
						# include image in weblog
						wlog.write('<br><img src="'+name.split('/')[-1]+'"n')
						# include command in weblog
						last = open('plotms.last', 'r')
						for line in last:
							pass
						wlog.write('<br>'+line[1:].split(',plotfile')[0]+')'+' \n')
						wlog.write('<br>\n')
						wlog.write('<br>\n')
						wlog.write('<hr>\n')
		breathe(resttime = 10)
		os.system('rm -rf *_3')
		wlog.close()

		#---------------------------------------
		#Check RFI of FLUXCAL2:
		#---------------------------------------
		wlog = open(wlogfile,"a+")
		if field_flux2:
			wlog.write('<h1>Plot flux calibrator 2 Amp vs Channel: </h1> \n')
			for ii in spw_id:
				name = os.path.join(plotdir,'flux_calibrator2_spw-'+str(ii)+'_channel-amp_after_calibration.png')
				file_exist = os.path.isfile(name) or os.path.isfile('weblog/'+name)
				if file_exist == True:
					print 'Plot '+name+' already exists.'
				else:
					print ii
					plotms(vis=ms_active,xaxis='channel',yaxis='amp',ydatacolumn='corrected',selectdata=True,field=field_flux2,spw=str(ii),scan='',correlation='RR,LL',averagedata=True,avgscan=False,transform=False,extendflag=False,iteraxis='',coloraxis='antenna1',plotrange=[],title='Flux Calibrator 2 Spw - '+str(ii)+' - channel vs. amp - after calibration ',xlabel='Channel',ylabel='Amplitude',showmajorgrid=True,showminorgrid=True,plotfile=name,overwrite=True,showgui=False)
					breathe()
					if wlog:
							# include image in weblog
							wlog.write('<br><img src="'+name.split('/')[-1]+'">\n')
							# include command in weblog
							last = open('plotms.last', 'r')
							for line in last:
								pass
							wlog.write('<br>'+line[1:].split(',plotfile')[0]+')'+' \n')
							wlog.write('<br>\n')
							wlog.write('<br>\n')
							wlog.write('<hr>\n')
			breathe(resttime = 10)
			os.system('rm -rf *_3')
		wlog.close()

		#---------------------------------------
		#Check RFI of GAINCAL 1:
		#---------------------------------------
		wlog = open(wlogfile,"a+")
		wlog.write('<h1>Plot gain calibrator 1 Amp vs. channel: </h1> \n')
		for ii in spw_id:
			name = os.path.join(plotdir,'gain_calibrator1_spw-'+str(ii)+'_channel-amp_after_calibration.png')
			file_exist = os.path.isfile(name) or os.path.isfile('weblog/'+name)
			if file_exist == True:
				print 'Plot '+name+' already exists.'
			else:
				print ii
				plotms(vis=ms_active,xaxis='channel',yaxis='amp',ydatacolumn='corrected',selectdata=True,field=field_gain1,spw=str(ii),scan='',correlation='RR,LL',averagedata=True,avgscan=False,transform=False,extendflag=False,iteraxis='',coloraxis='antenna1',plotrange=[],title='Gain Calibrator 1 Spw - '+str(ii)+' - channel vs. amp - after calibration',xlabel='Channel',ylabel='Amplitude',showmajorgrid=True,showminorgrid=True,plotfile=name,overwrite=True,showgui=False)
				breathe()
				if wlog:
						# include image in weblog
						wlog.write('<br><img src="'+name.split('/')[-1]+'">\n')
						# include command in weblog
						last = open('plotms.last', 'r')
						for line in last:
							pass
						wlog.write('<br>'+line[1:].split(',plotfile')[0]+')'+' \n')
						wlog.write('<br>\n')
						wlog.write('<br>\n')
						wlog.write('<hr>\n')
		breathe(resttime = 10)
		os.system('rm -rf *_3')
		wlog.close()

		#---------------------------------------
		#Check RFI of GAINCAL 2:
		#---------------------------------------
		wlog = open(wlogfile,"a+")
		if field_gain2:
			wlog.write('<h1>Plot gain calibrator 2 Amp vs. channel: </h1> \n')
			for ii in spw_id:
				name = os.path.join(plotdir,'gain_calibrator2_spw-'+str(ii)+'_channel-amp_after_calibration.png')
				file_exist = os.path.isfile(name) or os.path.isfile('weblog/'+name)
				if file_exist == True:
					print 'Plot '+name+' already exists.'
				else:
					print ii
					plotms(vis=ms_active,xaxis='channel',yaxis='amp',ydatacolumn='corrected',selectdata=True,field=field_gain2,spw=str(ii),scan='',correlation='RR,LL',averagedata=True,avgscan=False,transform=False,extendflag=False,iteraxis='',coloraxis='antenna1',plotrange=[],title='Gain Calibrator 2 Spw - '+str(ii)+' - channel vs. amp - after calibration',xlabel='Channel',ylabel='Amplitude',showmajorgrid=True,showminorgrid=True,plotfile=name,overwrite=True,showgui=False)
					breathe()
					if wlog:
							# include image in weblog
							wlog.write('<br><img src="'+name.split('/')[-1]+'">\n')
							# include command in weblog
							last = open('plotms.last', 'r')
							for line in last:
								pass
							wlog.write('<br>'+line[1:].split(',plotfile')[0]+')'+' \n')
							wlog.write('<br>\n')
							wlog.write('<br>\n')
							wlog.write('<hr>\n')
			breathe(resttime = 10)
			os.system('rm -rf *_3')
		wlog.close()

		#---------------------------------------
		#Check Amp vs. Scan of FLUXCAL 1:
		#---------------------------------------
		wlog = open(wlogfile,"a+")
		wlog.write('<h1>Plot flux calibrator 1 Amp vs Time: </h1> \n')
		for ii in spw_id:
			name = os.path.join(plotdir,'flux_calibrator1_spw-'+str(ii)+'_amp-time_after_calibration.png')
			file_exist = os.path.isfile(name) or os.path.isfile('weblog/'+name)
			if file_exist == True:
				print 'Plot '+name+' already exists.'
			else:
				print ii
				plotms(vis=ms_active,xaxis='time',yaxis='amp',ydatacolumn='corrected',selectdata=True,field=field_flux1,spw=str(ii),scan='',correlation='RR,LL',averagedata=True,avgscan=False,transform=False,extendflag=False,iteraxis='',coloraxis='antenna1',plotrange=[],title='Flux Calibrator 1 Spw - '+str(ii)+' - amp vs. time - after calibration',xlabel='Time',ylabel='Amplitude',showmajorgrid=False,showminorgrid=False,plotfile=name,overwrite=True,showgui=False)
				breathe()
				if wlog:
						# include image in weblog
						wlog.write('<br><img src="'+name.split('/')[-1]+'">\n')
						# include command in weblog
						last = open('plotms.last', 'r')
						for line in last:
							pass
						wlog.write('<br>'+line[1:].split(',plotfile')[0]+')'+' \n')
						wlog.write('<br>\n')
						wlog.write('<br>\n')
						wlog.write('<hr>\n')
			breathe(resttime = 10)
			os.system('rm -rf *_3')
		wlog.close()

		#---------------------------------------
		#Check Amp vs. Time of FLUXCAL 2:
		#---------------------------------------
		wlog = open(wlogfile,"a+")
		if field_flux2:
			wlog.write('<h1>Plot flux calibrator 2 Amp vs Time: </h1> \n')
			for ii in spw_id:
				name = os.path.join(plotdir,'flux_calibrator2_spw-'+str(ii)+'_amp-time_after_calibration.png')
				file_exist = os.path.isfile(name) or os.path.isfile('weblog/'+name)
				if file_exist == True:
					print 'Plot '+name+' already exists.'
				else:
					print ii
					plotms(vis=ms_active,xaxis='time',yaxis='amp',ydatacolumn='corrected',selectdata=True,field=field_flux2,spw=str(ii),scan='',correlation='RR,LL',averagedata=True,avgscan=False,transform=False,extendflag=False,iteraxis='',coloraxis='antenna1',plotrange=[],title='Flux Calibrator 2 Spw - '+str(ii)+' - amp vs. time - after calibration',xlabel='Time',ylabel='Amplitude',showmajorgrid=False,showminorgrid=False,plotfile=name,overwrite=True,showgui=False)
					breathe()
					if wlog:
							# include image in weblog
							wlog.write('<br><img src="'+name.split('/')[-1]+'">\n')
							# include command in weblog
							last = open('plotms.last', 'r')
							for line in last:
								pass
							wlog.write('<br>'+line[1:].split(',plotfile')[0]+')'+' \n')
							wlog.write('<br>\n')
							wlog.write('<br>\n')
							wlog.write('<hr>\n')
			breathe(resttime = 10)
			os.system('rm -rf *_3')
		wlog.close()

		#---------------------------------------
		#Check Amp vs. Scan of GAINCAL1 :
		#---------------------------------------
		wlog = open(wlogfile,"a+")
		wlog.write('<h1>Plot gain calibrator 1 Amp vs Time: </h1> \n')
		for ii in spw_id:
				name = os.path.join(plotdir,'gain_calibrator1_spw-'+str(ii)+'_amp-time_after_calibration.png')
				file_exist = os.path.isfile(name) or os.path.isfile('weblog/'+name)
				if file_exist == True:
					print 'Plot '+name+' already exists.'
				else:
					print ii
					plotms(vis=ms_active,xaxis='time',yaxis='amp',ydatacolumn='corrected',selectdata=True,field=field_gain1,spw=str(ii),scan='',correlation='RR,LL',averagedata=True,avgscan=False,transform=False,extendflag=False,iteraxis='',coloraxis='antenna1',plotrange=[],title='Gain Calibrator 1 Spw - '+str(ii)+' - amp vs. time - after calibration',xlabel='Time',ylabel='Amplitude',showmajorgrid=False,showminorgrid=False,plotfile=name,overwrite=True,showgui=False)
					breathe()
					if wlog:
						# include image in weblog
						wlog.write('<br><img src="'+name.split('/')[-1]+'">\n')
						# include command in weblog
						last = open('plotms.last', 'r')
						for line in last:
							pass
						wlog.write('<br>'+line[1:].split(',plotfile')[0]+')'+' \n')
						wlog.write('<br>\n')
						wlog.write('<br>\n')
						wlog.write('<hr>\n')
		breathe(resttime = 10)
		os.system('rm -rf *_3')
		wlog.close()

		#---------------------------------------
		#Check Amp vs. Scan of GAINCAL:
		#---------------------------------------
		wlog = open(wlogfile,"a+")
		if field_gain2:
			wlog.write('<h1>Plot gain calibrator 2 Amp vs Time: </h1> \n')
			for ii in spw_id:
				name = os.path.join(plotdir,'gain_calibrator2_spw-'+str(ii)+'_amp-time_after_calibration.png')
				file_exist = os.path.isfile(name) or os.path.isfile('weblog/'+name)
				if file_exist == True:
					print 'Plot '+name+' already exists.'
				else:
					print ii
					plotms(vis=ms_active,xaxis='time',yaxis='amp',ydatacolumn='corrected',selectdata=True,field=field_gain1,spw=str(ii),scan='',correlation='RR,LL',averagedata=True,avgscan=False,transform=False,extendflag=False,iteraxis='',coloraxis='antenna1',plotrange=[],title='Gain Calibrator 2 Spw - '+str(ii)+' - amp vs. time - after calibration',xlabel='Time',ylabel='Amplitude',showmajorgrid=False,showminorgrid=False,plotfile=name,overwrite=True,showgui=False)
					breathe()
					if wlog:
							# include image in weblog
							wlog.write('<br><img src="'+name.split('/')[-1]+'">\n')
							# include command in weblog
							last = open('plotms.last', 'r')
							for line in last:
								pass
							wlog.write('<br>'+line[1:].split(',plotfile')[0]+')'+' \n')
							wlog.write('<br>\n')
							wlog.write('<br>\n')
							wlog.write('<hr>\n')
			breathe(resttime = 10)
			os.system('rm -rf *_3')
		wlog.close()

		#---------------------------------------
		#Bandpass solutions:
		#---------------------------------------
		#Plot final bandpass solution for each antenna seperately:
		#---------------------------------------
		wlog = open(wlogfile,"a+")
		wlog.write('<h1>Plot Bandpass solution: </h1> \n')
		for n,j in bp_id.items():
			wlog.write('<h2>SPW '+n+': </h2> \n')
			for ii in range(nplots):
				name = os.path.join(plotdir,'final_bp_amp_spw-'+n+'_plot-'+str(ii)+'.png')
				file_exist = os.path.isfile(name) or os.path.isfile('weblog/'+name)
				if file_exist == True:
					print 'Plot '+name+' already exists.'
				else:
					antPlot=str(ii*3)+'~'+str(ii*3+2)
					plotms(vis=glob.glob(os.path.join(caltabledir,'*finalBPcal*'))[0],xaxis='freq',yaxis='amp',spw=j,antenna = antPlot,iteraxis='antenna',coloraxis='corr',plotfile=name,xlabel='Freq',ylabel='Amplitude',showmajorgrid=True,showminorgrid=True,overwrite=True,showgui=False, gridrows=3)
					breathe(resttime = 2)
					os.system('mv '+name.split('.png')[0]+'* '+name)
					if wlog:
						# include image in weblog
						wlog.write('<br><img src="'+name.split('/')[-1]+'">\n')
						# include command in weblog
						last = open('plotms.last', 'r')
						for line in last:
							pass
						wlog.write('<br>'+line[1:].split(',plotfile')[0]+')'+' \n')
						wlog.write('<br>\n')
						wlog.write('<br>\n')
						wlog.write('<hr>\n')
			breathe(resttime = 2)
			os.system('rm -rf *_3')
		wlog.close()

		#---------------------------------------
		#Plot SNR final bandpass solution for each antenna seperately:
		#---------------------------------------
		wlog = open(wlogfile,"a+")
		wlog.write('<h1>Plot Bandpass SNR: </h1> \n')
		for n,j in bp_id.items():
			wlog.write('<h2>SPW '+n+': </h2> \n')
			for ii in range(nplots):
				name = os.path.join(plotdir,'final_bp_snr_spw-'+n+'_plot-'+str(ii)+'.png')
				file_exist = os.path.isfile(name) or os.path.isfile('weblog/'+name)
				if file_exist == True:
					print 'Plot '+name+' already exists.'
				else:
					antPlot=str(ii*3)+'~'+str(ii*3+2)
					plotms(vis=glob.glob(os.path.join(caltabledir,'*finalBPcal*'))[0],xaxis='freq',yaxis='snr',spw=j,antenna = antPlot,iteraxis='antenna',coloraxis='corr',plotfile=name,xlabel='Freq',ylabel='SNR',showmajorgrid=True,showminorgrid=True,overwrite=True,showgui=False, gridrows=3)
					breathe(resttime = 2)
					os.system('mv '+name.split('.png')[0]+'* '+name)
					if wlog:
						# include image in weblog
						wlog.write('<br><img src="'+name.split('/')[-1]+'">\n')
						# include command in weblog
						last = open('plotms.last', 'r')
						for line in last:
							pass
						wlog.write('<br>'+line[1:].split(',plotfile')[0]+')'+' \n')
						wlog.write('<br>\n')
						wlog.write('<br>\n')
						wlog.write('<hr>\n')
			breathe(resttime = 2)
			os.system('rm -rf *_3')
		wlog.close()

		#---------------------------------------
		#GAIN solutions:
		#---------------------------------------
		#Plot final amp gain solution for each antenna seperately:
		#---------------------------------------
		wlog = open(wlogfile,"a+")
		wlog.write('<h1>Plot Amp Gain solution: </h1> \n')
		for n,j in gain_id.items():
			wlog.write('<h2>SPW '+n+': </h2> \n')
			for ii in range(nplots):
				name = os.path.join(plotdir,'final_gain_amp_spw-'+n+'_plot-'+str(ii)+'.png')
				file_exist = os.path.isfile(name) or os.path.isfile('weblog/'+name)
				if file_exist == True:
					print 'Plot '+name+' already exists.'
				else:
					antPlot=str(ii*3)+'~'+str(ii*3+2)
					plotms(vis=glob.glob(os.path.join(caltabledir,'*finalampgaincal*'))[0],xaxis='scan',yaxis='amp',spw=j,antenna = antPlot,iteraxis='antenna',coloraxis='spw',plotfile=name,xlabel='Scan',ylabel='Amplitude Gain',showmajorgrid=True,showminorgrid=True,overwrite=True,showgui=False, gridrows=3, xconnector='line', timeconnector=True, plotrange=[0,0,0.9,1.1])
					breathe(resttime = 2)
					os.system('mv '+name.split('.png')[0]+'* '+name)
					if wlog:
						# include image in weblog
						wlog.write('<br><img src="'+name.split('/')[-1]+'">\n')
						# include command in weblog
						last = open('plotms.last', 'r')
						for line in last:
							pass
						wlog.write('<br>'+line[1:].split(',plotfile')[0]+')'+' \n')
						wlog.write('<br>\n')
						wlog.write('<br>\n')
						wlog.write('<hr>\n')
			breathe(resttime = 10)
			os.system('rm -rf *_3')
		wlog.close()

		#---------------------------------------
		#Plot phase amp gain solution for each antenna seperately:
		#---------------------------------------
		wlog = open(wlogfile,"a+")
		wlog.write('<h1>Plot Phase Gain solution: </h1> \n')
		for n,j in gain_id.items():
			wlog.write('<h2>SPW '+n+': </h2> \n')
			for ii in range(nplots):
				name = os.path.join(plotdir,'final_gain_phase_spw-'+n+'_plot-'+str(ii)+'.png')
				file_exist = os.path.isfile(name) or os.path.isfile('weblog/'+name)
				if file_exist == True:
					print 'Plot '+name+' already exists.'
				else:
					antPlot=str(ii*3)+'~'+str(ii*3+2)
					plotms(vis=glob.glob(os.path.join(caltabledir,'*finalphasegaincal*'))[0],xaxis='scan',yaxis='phase',spw=j,antenna = antPlot,iteraxis='antenna',coloraxis='spw',plotfile=name,xlabel='Scan',ylabel='Amplitude Phase',showmajorgrid=True,showminorgrid=True,overwrite=True,showgui=False, gridrows=3, xconnector='line', timeconnector=True, plotrange=[0,0,-50.,50.])
					breathe(resttime = 2)
					os.system('mv '+name.split('.png')[0]+'* '+name)
					if wlog:
						# include image in weblog
						wlog.write('<br><img src="'+name.split('/')[-1]+'">\n')
						# include command in weblog
						last = open('plotms.last', 'r')
						for line in last:
							pass
						wlog.write('<br>'+line[1:].split(',plotfile')[0]+')'+' \n')
						wlog.write('<br>\n')
						wlog.write('<br>\n')
						wlog.write('<hr>\n')
			breathe(resttime = 2)
			os.system('rm -rf *_3')
		wlog.close()

	except:
			raise

###########################
#### main
###########################

# execfile  "/data/beegfs/astro-storage/groups/walter/novak/scripts/vla/make_quality_images_cals.py"

ms_active="13A-213.sb20683830.eb21918128.56427.38029568287.ms"

#--> MODIFY (just update the spws for each science objective)
plot_dic = {
		'CONT': '0,2,3,5,6,7',
		'HI': '8',
		'OH': '11,12,13,15',
		'RRL': '9,10,14,16,17,18,19',
}

#--> MODIFY (for re-usability, I included this script in the casa_pipescript.py file with execfile('path-to-my-file/make_quality_images_cals.py'). I specify the sdm file I was working on with ms_active before executing this script. IF NOT NEEDED REMOVE)
# check if ms_active is actually an ms file
if (not ms_active.split('.')[-1] =='ms'):
		ms_active = ms_active+'.ms'

# execute (MODIFY accordingly)
wlog = make_plots(ms_active, # ms file
				  caltabledir='./', # location of the calibration tables
				  plotdir='./quality_images/', # new directory for the .png files (will be created)
				  spw_id=np.arange(20), # total number of spw in the setup
				  field_flux1 = '1', #field of the flux/bandpass calibrator
				  field_flux2 = None, #field of a second flux/bandpass calibrator (None if not applicable)
				  field_gain1 ='2', # field for complex gain calibrator
				  field_gain2 =None, # field of second complex gain calib (None if not applicable)
				  plot_dic = plot_dic, # see above
				  wlogfile=False # in case there is another weblog this should be added to (just leave False)
				  )

