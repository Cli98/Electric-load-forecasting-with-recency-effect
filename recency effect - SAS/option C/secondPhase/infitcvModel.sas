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

%MACRO modifyinput(id,id2,h,d,hour);
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
%if not %sysfunc(exist(maintemperature_&h._&d)) %then %do;
	create table maintemperature_&h._&d as
	select monotonic() as trend,year,month,day,hour,weekday(mdy(month,day,year)) as weekday,
	* from lag_a&id;
	
	create table traintemperature_&h._&d as
	select * from maintemperature_&h._&d
	where year in (2004,2005);
	*do not rebuild cvset for option C;
	create table cvtemperature_&h._&d as
	select * from maintemperature_&h._&d
	where year=2006;
%end;
quit;

%trainconcat(&id,&id2);
proc sql;
create table cvtemperature_&h._&d._&hour as
select * from cvtemperature_&h._&d
where hour=&hour;

proc append base=insample&id&id2 data=cvtemperature_&h._&d._&hour;
run;
%infitcv(&id,&id2,&h,&d,&hour);
%MEND;
		
%MACRO trainconcat(id,id2);
data insample&id&id2;
set traintemperature_&h._&d;
set trainload&id2; 
run;
%Mend;

%MACRO infitcv(id,id2,h,d,hour);

	data insample_&h._&d._&hour;
	set insample&id&id2(drop=trend);
	*option C dont modify here;
	run;

	proc sql;
	create table insample_&h._&d._&hour as
	select monotonic() as trend,* from insample_&h._&d._&hour;
	quit;

	proc sql;
		create table pre_&h._&d._&hour as
		select * from insample_&h._&d._&hour;
	quit;
	proc glm data=pre_&h._&d._&hour noprint;
		class hour weekday month;
		model load = trend hour weekday month hour*weekday &mname /SINGULAR=10e-4;
		output out=res predicted=ypre;
	run; 
	proc sql;
		create table temp as
		select monotonic() as id,ypre from res
		where load=. and hour=&hour;

		create table temp2 as
		select monotonic() as id,load from cvload&id2
		where hour=&hour;

		create table cb as
		select temp.ypre,temp2.load
		from temp,temp2
		where temp.id = temp2.id;
		
		create table MAPE as
		select distinct sum(abs((load-ypre))/load)/count(*)*100 as mape 
		from cb;
	quit;
	
	%if not %sysfunc(exist(cvmapesum_&hour)) %then %do;
	data cvmapesum_&hour;
		set MAPE;
		run;
	%end;
	%else %do;
	proc append base=cvmapesum_&hour data=MAPE;
	run;
	%end;

%Mend;

%MACRO trainload(id);
proc sql;
create table trainload&id as
	select year,month,day,hour,sum(load) as load from repro.load
	where year in (2004,2005)
	group by year,month,day,hour;
quit;
%MEND;

%MACRO cvload(id);
proc sql;
create table cvload&id as
	select year,month,day,hour,sum(load) as load from repro.load
	where year in (2006)
	group by year,month,day,hour;
quit;
%MEND;

%MACRO loopAcv(zone,h1,d1);
    %global mname;
    %trainload(&zone);*name: trainload&id;
    %cvload(&zone);*name: cvload&id;
	%do hour=1 %to 24;
    %do d=0 %to &d1;
    	%do h=0 %to &h1;
			%modifyinput(11,&zone,&h,&d,&hour);
    	%end;
	%end;
	proc sql;
	create table f as 
	select monotonic() as id, mape from cvmapesum_&hour;
	quit;
	proc sql outobs=1;
	create table cvmapesum_&hour._col as 
	select id, mape as minmape from f
	where mape = (select min(mape) from f);
	quit;
	%if not %sysfunc(exist(repro.paracv)) %then %do;
	data repro.paracv;
		set cvmapesum_&hour._col;
		run;
	%end;
	%else %do;
	proc append base=repro.paracv data=cvmapesum_&hour._col;
	run;
	%end;
	%end;
	data repro.paracv(drop=hour);
	set repro.paracv;
	do hour=1 to 24;
	h = int(id/%eval(&h1+1));
	d = mod(id,%eval(&h1+1));
	end;
	output;
	run;
%Mend;


