Summary:	A modern, advanced and high performance authoritative-only nameserver
Name:		pdns
Version:	2.9.20
Release:	5%{?dist}

Group:		System Environment/Daemons
License:	GPL
URL:		http://powerdns.com
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Source0:	http://downloads.powerdns.com/releases/%{name}-%{version}.tar.gz
Patch0:		%{name}-fixinit.patch
Patch1:		%{name}-avoid-version.patch

BuildRequires:	boost-devel, chrpath
Provides:	powerdns = %{version}-%{release}

%description
The PowerDNS Nameserver is a modern, advanced and high performance
authoritative-only nameserver. It is written from scratch and conforms
to all relevant DNS standards documents.
Furthermore, PowerDNS interfaces with almost any database.

%package	backend-mysql
Summary:	MySQL backend for %{name}
Group:		System Environment/Daemons
Requires:	%{name} = %{version}-%{release}
BuildRequires:	mysql-devel

%package	backend-postgresql
Summary:	PostgreSQL backend for %{name}
Group:		System Environment/Daemons
Requires:	%{name} = %{version}-%{release}
BuildRequires:	postgresql-devel

%package	backend-pipe
Summary:	Pipe backend for %{name}
Group:		System Environment/Daemons
Requires:	%{name} = %{version}-%{release}

%package	backend-geo
Summary:	Geo backend for %{name}
Group:		System Environment/Daemons
Requires:	%{name} = %{version}-%{release}

%package	backend-ldap
Summary:	LDAP backend for %{name}
Group:		System Environment/Daemons
Requires:	%{name} = %{version}-%{release}
BuildRequires:	openldap-devel

%description	backend-mysql
This package contains the gmysql backend for %{name}

%description	backend-postgresql
This package contains the gpgsql backend for %{name}

%description	backend-pipe
This package contains the pipe backend for %{name}

%description	backend-geo
This package contains the geo backend for %{name}
It allows different answers to DNS queries coming from different
IP address ranges or based on the geographic location

%description	backend-ldap
This package contains the ldap backend for %{name}


%prep
%setup -q
%patch0 -p1 -b .fixinit
%patch1 -p1 -b .avoid-version

%build
export CPPFLAGS="-DLDAP_DEPRECATED %{optflags}"

%configure \
	--sysconfdir=%{_sysconfdir}/%{name} \
	--libdir=%{_libdir}/%{name} \
	--disable-static \
	--with-modules='' \
	--with-dynmodules='pipe gmysql gpgsql geo ldap' \
	--with-mysql-includes=%{_includedir}/mysql \
	--with-mysql-lib=%{_libdir}/mysql \
	--with-pgsql-includes=%{_includedir} \
	--with-pgsql-lib=%{_libdir}

make %{?_smp_mflags}

%install
%{__rm} -rf %{buildroot}
make install DESTDIR=%{buildroot}

%{__rm} -f %{buildroot}%{_libdir}/%{name}/*.la
%{__install} -p -D -m 0755 pdns/pdns %{buildroot}%{_initrddir}/pdns
%{__mv} %{buildroot}%{_sysconfdir}/%{name}/pdns.conf{-dist,}

# strip the static rpath from the binaries
chrpath --delete %{buildroot}%{_bindir}/pdns_control
chrpath --delete %{buildroot}%{_bindir}/zone2ldap
chrpath --delete %{buildroot}%{_bindir}/zone2sql
chrpath --delete %{buildroot}%{_sbindir}/pdns_server
chrpath --delete %{buildroot}%{_libdir}/%{name}/*.so

%post
if [ $1 = 1 ]; then
	/sbin/chkconfig --add pdns
	%{_sbindir}/useradd -c "PowerDNS user" -s /sbin/nologin -r -d / pdns
fi
%preun
if [ "$1" = 0 ]; then
	/sbin/service pdns stop >/dev/null 2>&1
	/sbin/chkconfig --del pdns
fi

%postun
if [ "$1" -ge "1" ]; then
	/sbin/service pdns reload >/dev/null 2>&1
fi

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-,root,root,-)
%doc ChangeLog TODO pdns/COPYING
%{_bindir}/pdns_control
%{_bindir}/zone2ldap
%{_bindir}/zone2sql
%{_sbindir}/pdns_server
%{_mandir}/man8/pdns_control.8.gz
%{_mandir}/man8/pdns_server.8.gz
%{_mandir}/man8/zone2sql.8.gz
%{_initrddir}/pdns
%dir %{_libdir}/%{name}/
%dir %{_sysconfdir}/%{name}/
%config(noreplace) %{_sysconfdir}/%{name}/pdns.conf

%files backend-mysql
%defattr(-,root,root,-)
%doc pdns/COPYING
%{_libdir}/%{name}/libgmysqlbackend.so

%files backend-postgresql
%defattr(-,root,root,-)
%doc pdns/COPYING
%{_libdir}/%{name}/libgpgsqlbackend.so

%files backend-pipe
%defattr(-,root,root,-)
%doc pdns/COPYING
%{_libdir}/%{name}/libpipebackend.so

%files backend-geo
%defattr(-,root,root,-)
%doc pdns/COPYING
%{_libdir}/%{name}/libgeobackend.so

%files backend-ldap
%defattr(-,root,root,-)
%doc pdns/COPYING
%{_libdir}/%{name}/libldapbackend.so


%changelog
* Sat Dec 30 2006 <ruben@rubenkerkhof.com> 2.9.20-5
- Strip rpath from the backends as well
* Fri Dec 29 2006 <ruben@rubenkerkhof.com> 2.9.20-4
- Disable rpath
* Thu Dec 28 2006 <ruben@rubenkerkhof.com> 2.9.20-3
- More fixes as per review #219973
* Wed Dec 27 2006 <ruben@rubenkerkhof.com> 2.9.20-2
- A few changes for FE review (bz #219973):
- Renamed package to pdns, since that's how upstream calls it
- Removed calls to ldconfig
- Subpackages now require %%{version}-%%{release}
* Sat Dec 16 2006 <ruben@rubenkerkhof.com> 2.9.20-1
- Initial import

