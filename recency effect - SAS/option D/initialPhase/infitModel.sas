%MACRO trainload(id);
proc sql;
create table trainload&id as
	select year,sum(load) as load from repro.load
	where year in (2004,2005)
	group by year,month,day,hour;
quit;
%MEND;

%MACRO traintemperature(id);
proc sql;
create table traintemperature&id as
	select * from repro.temperature
	where station_id=&id and year in (2004,2005);
%Mend;

%MACRO trainconcat(id1,id2);
*id2=21 in this case;
data insample&id1&id2(drop=station_id year);
set traintemperature&id1;
set trainload&id2;
run;
%Mend;

%MACRO infit(id1,id2);
	*id2=21 in this case;
	proc glm data=insample&id1&id2;
		class hour weekday month;
		model load = trend hour weekday month tem tems temc hour*weekday tem*hour tems*hour temc*hour
		tem*month tems*month temc*month/SINGULAR=10e-10;
		output out=res predicted=ypre;
	run; 
	proc sql;
		create table MAPE as
		select distinct sum(abs((load-ypre))/load)/count(*)*100 as mape
		from res;
	quit;
	proc append base=repro.MAPEsum data=MAPE;
	run;
%Mend;

%MACRO loopA(zone);
	*zone=21 in this case;
	%trainload(&zone);
	%do id=1 %to 11;
		%traintemperature(&id);
		%trainconcat(&id,&zone);
		%infit(&id,&zone);
	%end;
%Mend;

%MACRO sortMAPE();	
	proc sql;
		create table MAPEnew as
		select monotonic() as obs, * from repro.mapesum;
	quit;
	proc sort data=MAPEnew out=repro.mapesum;
		by mape;
	run;
%Mend;
