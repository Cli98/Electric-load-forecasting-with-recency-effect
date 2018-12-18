%MACRO addseq(n);
%global seq;
proc sql inobs=&n noprint;
	select obs 
	into :seq separated by ','
	from repro.mapesum;
quit;
%MEnd;

%macro shift(h,d);
proc expand data=a&id out=a&id method=none;
id Date;
%do i=1 %to &h;
	convert tem = tem_lag&i / transformout = (lag &i);
%end;
%do i=1 %to &d;
	convert tem = tem_movave&i / transformout = (movave %eval(&i*24) trim %eval(&i*24-1));
%end;
run;
%mend;

%MACRO modifyinput(id,id2,h,d);
*this function is required to pick items in seq1-id
add them up and average temperature.;
%addseq(&id);
%trainload(&id2);
%cvload(&id2);
proc sql;
	create table a&id as
	select DHMS(MDY(month,day,year),hour,0,0) as Date ,year,month,day,hour,sum(tem)*1.0/&id as tem,(sum(tem)*1.0/&id)**2 as tem2,(sum(tem)*1.0/&id)**3 as tem3 from repro.temperature
	where station_id in (&seq)
	group by year,month,day,hour
	order by year,month,day,hour;
quit;	
%let mname = %STR(tem tem2 tem3 tem*month tem2*month tem3*month tem*hour tem2*hour tem3*hour);

%shift(&h,&d);

data lag_a&id;
	set a&id;
   %do n=1 %to &h;
	   tem_lag&n.s = tem_lag&n**2;
	   tem_lag&n.c = tem_lag&n**3;
	   %let mname = &mname tem_lag&n tem_lag&n.s tem_lag&n.c 
	   tem_lag&n*month tem_lag&n.s*month tem_lag&n.c*month
	   tem_lag&n*hour tem_lag&n.s*hour tem_lag&n.c*hour;
   %end;
   %do n=1 %to &d;
	   tem_movave&n.s = tem_movave&n**2;
	   tem_movave&n.c = tem_movave&n**3;
	   %let mname = &mname tem_movave&n tem_movave&n.s tem_movave&n.c 
	   tem_movave&n*month tem_movave&n.s*month tem_movave&n.c*month
	   tem_movave&n*hour tem_movave&n.s*hour tem_movave&n.c*hour;
   %end;

proc sql;	
	create table maintemperature&id as
	select monotonic() as trend,year,month,day,hour,weekday(mdy(month,day,year)) as weekday,
	* from lag_a&id;
	
	create table traintemperature&id as
	select * from maintemperature&id
	where year in (2004,2005);
	
	create table cvtemperature&id as
	select * from maintemperature&id
	where year=2006;
quit;

%trainconcat(&id,&id2);
proc append base=insample&id&id2 data=cvtemperature&id;
run;
%infitcv(&id,&id2,&h,&d);
%MEND;
		
%MACRO trainconcat(id,id2);
data insample&id&id2;
set traintemperature&id;
set trainload&id2; 
run;
%Mend;

%MACRO infitcv(id1,id2,h,d);

	data insample&id1&id2;
	set insample&id1&id2(drop=trend);
	run;
	proc sql;
	create table insample&id1&id2 as
	select monotonic() as trend,* from insample&id1&id2;
	quit;
	proc glm data=insample&id1&id2 noprint;
		class hour weekday month;
		model load = trend hour weekday month hour*weekday &mname /SINGULAR=10e-10;
		output out=res predicted=ypre;
	run; 
	proc sql;
		create table temp as
		select monotonic() as id,ypre from res
		where load=.;

		create table temp2 as
		select monotonic() as id,load from cvload&id2;

		create table cb as
		select temp.ypre,temp2.load
		from temp,temp2
		where temp.id = temp2.id;
		
		create table MAPE as
		select distinct sum(abs((load-ypre))/load)/count(*)*100 as mape 
		from cb;
	quit;
	
	%if not %sysfunc(exist(repro.cvmapesum)) %then %do;
	data repro.cvmapesum;
		set MAPE;
		run;
	%end;
	%else %do;
	proc append base=repro.cvmapesum data=MAPE;
	run;
	%end;
	
%Mend;

%MACRO trainload(id);
proc sql;
create table trainload&id as
	select year,sum(load) as load from repro.load
	where year in (2004,2005)
	group by year,month,day,hour;
quit;
%MEND;

%MACRO cvload(id);
proc sql;
create table cvload&id as
	select year,sum(load) as load from repro.load
	where year in (2006)
	group by year,month,day,hour;
quit;
%MEND;

%MACRO loopAcv(zone,hg,dg);
    %global mname;
    %trainload(&zone);*name: trainload&id;
    %cvload(&zone);*name: cvload&id;
    %do d=0 %to 3;
    %do h=0 %to 7;
    %modifyinput(11,&zone,&h,&d);
    %end;
    %end;
%Mend;


