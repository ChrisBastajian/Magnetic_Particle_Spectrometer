%%Initializing paramaters:
t = linspace(0, 1/(1000), 1000000);
f = 1./t;
beta = 1000; %beta = u0m*T % 
f_drive = 1000; % 1 kHz
w_drive = 2 * pi * f_drive;
Hd = 25 * (10^(-3)); %25 mT amplitude
H_DC = 0 * (10^(-3)); % in mT
cm = 1; %concentration * magnetic moment

H_AC = Hd * cos(w_drive .*t); %pure AC field without DC offset in x 

%%This is the magnetic field applied to the sample:
H = Hd * cos(w_drive .*t) + H_DC;
H_mag = ((H_DC.^2) + (H_AC.^2)).^(0.5); %the magnitude of the field (what is actually used)
beta_H_mag = beta .* H_mag; %this is what is used in langevin function

%plot(t, H_mag);

%%This is the magnetization M(t):
M_mag = cm * coth(beta_H_mag) - 1./(beta_H_mag); 
%plot(t, M_mag);


%%This is the numerical result of dM/dt
dMdt = gradient(M_mag)./gradient(t); 
%dMdt = dMdt./max(dMdt); % to normalize
plot(t, dMdt);
hold on

%%This is the calculated dMdt by hand:
% dHacdt = -w_drive .*Hd .*sin(w_drive .*t); %The time differential of the ac component
% %dindt = (beta .* dHacdt)./H_mag; %derivative of the inner function
% 
% common_factors = cm .*dindt; %when factoring out all common factors this is what we get
% 
% dMdt_calc = common_factors .*(((csch(beta_H_mag)).^2) + (1./((beta^2).*(H_mag.^2))));
% 
% 
% %plot(t, dMdt_calc);

dM_mag_dt = cm * (-csch(beta .* sqrt(H_DC.^2 + (Hd .* cos(w_drive .* t)).^2)).^2 + 1 ./ (beta.^2 .* (H_DC.^2 + (Hd .* cos(w_drive .* t)).^2))) .* (-beta .* Hd.^2 .* w_drive .* sin(w_drive .* t) .* cos(w_drive .* t) ./ sqrt(H_DC.^2 + (Hd .* cos(w_drive .* t)).^2));

plot(t, dM_mag_dt, LineStyle="--"); % the time differential of the total magnitude of the magnetization
hold off

%%What we really want is dMzdt:
Hz_unit = H_AC ./H_mag; %the z component of the unit vector of the entire field with respect to time
Mz = cm * (coth(beta_H_mag) - 1./(beta_H_mag)) .*Hz_unit;

dMzdt_num = gradient(Mz)./ gradient(t);
plot(t, dMzdt_num);
hold on

%analytically solving, Mz = M_mag * Hz_unit in the z direction
dH_magdt = (-Hd.^2 .* w_drive .* cos(w_drive .*t) .* sin(w_drive .*t))./H_mag; %the time differential of the magnetic field's magnitude

dHzdt = -Hd .* w_drive .* sin(w_drive .*t); %the time differential of the z component of the field (d(H_AC)/dt)

dHz_unit_dt = (dHzdt .* H_mag - dH_magdt .* H_AC) ./ (H_mag .^2);

dMzdt_calc = dM_mag_dt .* Hz_unit + dHz_unit_dt .* M_mag;

plot(t, dMzdt_calc, LineWidth=1);

%%Rewriting the full expression with no intermediate variable substitutions
%%then simplifying

dMzdt_calc_full = cm * ((-csch(beta .* sqrt(H_DC.^2 + (Hd .* cos(w_drive .* t)).^2)).^2 + 1 ./ (beta.^2 .* (H_DC.^2 + (Hd .* cos(w_drive .* t)).^2))) .* ...
    (-beta .* Hd.^2 .* w_drive .* sin(w_drive .* t) .* cos(w_drive .* t) ./ sqrt(H_DC.^2 + (Hd .* cos(w_drive .* t)).^2)) .* ...
    (Hd .* cos(w_drive .* t)) ./ sqrt(H_DC.^2 + (Hd .* cos(w_drive .* t)).^2)) + ...
    ((-Hd .* w_drive .* sin(w_drive .* t) .* sqrt(H_DC.^2 + (Hd .* cos(w_drive .* t)).^2) - ...
    ((-Hd.^2 .* w_drive .* cos(w_drive .* t) .* sin(w_drive .* t)) ./ sqrt(H_DC.^2 + (Hd .* cos(w_drive .* t)).^2)) .* Hd .* cos(w_drive .* t)) ./ ...
    (H_DC.^2 + (Hd .* cos(w_drive .* t)).^2)) .* ...
    (cm * (coth(beta .* sqrt(H_DC.^2 + (Hd .* cos(w_drive .* t)).^2)) - 1 ./ (beta .* sqrt(H_DC.^2 + (Hd .* cos(w_drive .* t)).^2))));

plot(t, dMzdt_calc_full, LineWidth= 2);
 %a  = dMzdt_calc_full ./dMzdt_calc %to check if they're equal

dMzdt_calc_simplified = cm * (-csch(beta_H_mag).^2 + 1 ./ (beta_H_mag.^2)) .* ...
    (-beta .* Hd.^2 .* w_drive .* sin(w_drive .* t) .* cos(w_drive .* t) ./ H_mag) .* Hz_unit + ...
    ((-Hd .* w_drive .* sin(w_drive .* t) .* H_mag - ((-Hd.^2 .* w_drive .* cos(w_drive .* t) .* sin(w_drive .* t)) ./ H_mag) .* Hd .* cos(w_drive .* t)) ./ (H_mag .^2)) .* ...
    (cm * (coth(beta_H_mag) - 1 ./ beta_H_mag));

b = dMzdt_calc_simplified ./dMzdt_calc_full;  %to check if they're equal


