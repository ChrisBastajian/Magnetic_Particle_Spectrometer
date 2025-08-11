

FWHM = 4.4; % Define Full Width Half Max of particle in mT
Beta = 4.16./FWHM; % Calculate Beta from FWHM of particle

f_drive = 1000;
Hd_amp = 25; % Amplitude of drive field (mT)

f_samp = 100000; % Sampling frequency of DAQ card (Hz)
N_periods = 100;  % Enter number of periods simulated


%%
t_step = 1./f_samp; % Calculate time step
T_drive = 1./f_drive; % Calculate period form drive coil
t_samp = 0:t_step:(N_periods.*T_drive); % time array

t_phys = 0:(t_step./10):(N_periods.*T_drive); % Make a time array that is 10 x finer than sampling rate to make numerical derivative more accurate
Hd = Hd_amp.*cos(2.*pi.*f_drive.*t_phys); % Calculate drive field

Hd_meas = interp1(t_phys,Hd,t_samp); % Interpolate H drive to match sampling array size

plot(Hd_meas);

M = coth(Beta.*Hd)-1./(Beta.*Hd);
dM_dt = gradient(M)./(t_phys(2)-t_phys(1));

V_meas = interp1(t_phys,dM_dt,t_samp);

plot(V_meas);
[harm_f,harm_mag,harm_phi] = chris_fft(V_meas,f_samp);

plot(harm_mag);