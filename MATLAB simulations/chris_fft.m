function [f,magnitude,phase] = chris_fft(x,fs)

y = fft(x);
N = length(x);          % number of samples
f = (0:N-1)*(fs/(N-1));     % frequency range

% Calculate the magnitude and phase of each harmonic
magnitude = abs(y) / (N);  % Normalizing the magnitude
phase = angle(y);

% Only return the first half of the FFT result since it is symmetric
% (for real signals)
magnitude = 2.*magnitude(1:floor(N/2)+1);
phase = phase(1:floor(N/2)+1);
f = f(1:floor(N/2)+1);

end