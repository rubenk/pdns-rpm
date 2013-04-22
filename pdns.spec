%global _hardened_build 1
%global backends %{nil}

Name: pdns
Version: 3.2
Release: 7%{?dist}
Summary: A modern, advanced and high performance authoritative-only nameserver
Group: System Environment/Daemons
License: GPLv2
URL: http://powerdns.com
Source0: http://downloads.powerdns.com/releases/%{name}-%{version}.tar.gz
Source1: pdns.service
Patch0: pdns-default-config.patch
Patch1: pdns-fixarm32.patch

Requires(pre): shadow-utils
Requires(post): systemd-sysv
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units

BuildRequires: systemd-units
BuildRequires: boost-devel
BuildRequires: lua-devel
BuildRequires: cryptopp-devel
BuildRequires: autoconf
BuildRequires: automake
BuildRequires: libtool
Provides: powerdns = %{version}-%{release}

%description
The PowerDNS Nameserver is a modern, advanced and high performance
authoritative-only nameserver. It is written from scratch and conforms
to all relevant DNS standards documents.
Furthermore, PowerDNS interfaces with almost any database.

%package	backend-mysql
Summary:	MySQL backend for %{name}
Group:		System Environment/Daemons
Requires:	%{name}%{?_isa} = %{version}-%{release}
BuildRequires:	mysql-devel
%global backends %{backends} gmysql

%package	backend-postgresql
Summary:	PostgreSQL backend for %{name}
Group:		System Environment/Daemons
Requires:	%{name}%{?_isa} = %{version}-%{release}
BuildRequires:	postgresql-devel
%global backends %{backends} gpgsql

%package	backend-pipe
Summary:	Pipe backend for %{name}
Group:		System Environment/Daemons
Requires:	%{name}%{?_isa} = %{version}-%{release}
%global backends %{backends} pipe

%package	backend-geo
Summary:	Geo backend for %{name}
Group:		System Environment/Daemons
Requires:	%{name}%{?_isa} = %{version}-%{release}
%global backends %{backends} geo

%package	backend-ldap
Summary:	LDAP backend for %{name}
Group:		System Environment/Daemons
Requires:	%{name}%{?_isa} = %{version}-%{release}
BuildRequires:	openldap-devel
%global backends %{backends} ldap

%package	backend-sqlite
Summary:	SQLite backend for %{name}
Group:		System Environment/Daemons
Requires:	%{name}%{?_isa} = %{version}-%{release}
BuildRequires:	sqlite-devel
%global backends %{backends} gsqlite3

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

%description	backend-sqlite
This package contains the SQLite backend for %{name}

%prep
%setup -q
%patch0 -p1 -b .default-config-patch
%patch1 -p1 -b .pdns-fixarm32

%build
autoreconf -v -f -i
export CPPFLAGS="-DLDAP_DEPRECATED"

%configure \
	--sysconfdir=%{_sysconfdir}/%{name} \
	--libdir=%{_libdir}/%{name} \
	--disable-static \
	--with-modules='' \
	--with-lua \
	--with-dynmodules='%{backends}' \
	--enable-cryptopp

sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

make %{?_smp_mflags}

%install
make install DESTDIR=%{buildroot}

%{__rm} -f %{buildroot}%{_libdir}/%{name}/*.la
%{__mv} %{buildroot}%{_sysconfdir}/%{name}/pdns.conf{-dist,}

chmod 600 %{buildroot}%{_sysconfdir}/%{name}/pdns.conf

# Copy systemd service file
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/pdns.service

%pre
getent group pdns >/dev/null || groupadd -r pdns
getent passwd pdns >/dev/null || \
	useradd -r -g pdns -d / -s /sbin/nologin \
	-c "PowerDNS user" pdns
exit 0

%post
%systemd_post pdns.service

%preun
%systemd_preun pdns.service

%postun
%systemd_postun_with_restart pdns.service

%triggerun -- pdns < 3.0-rc3
# Save the current service runlevel info
# User must manually run systemd-sysv-convert --apply pdns
# to migrate them to systemd targets
%{_bindir}/systemd-sysv-convert --save pdns &>/dev/null ||:

# Run these because the SysV package being removed won't do them
/sbin/chkconfig --del pdns &>/dev/null || :
/bin/systemctl try-restart pdns.service &>/dev/null || :

%files
%defattr(-,root,root,-)
%doc COPYING README
%{_bindir}/dnsreplay
%{_bindir}/pdns_control
%{_bindir}/pdnssec
%{_bindir}/zone2ldap
%{_bindir}/zone2sql
%{_bindir}/zone2json
%{_sbindir}/pdns_server
%{_mandir}/man8/pdns_control.8.gz
%{_mandir}/man8/pdns_server.8.gz
%{_mandir}/man8/zone2sql.8.gz
%{_unitdir}/pdns.service
%dir %{_libdir}/%{name}/
%dir %{_sysconfdir}/%{name}/
%config(noreplace) %{_sysconfdir}/%{name}/pdns.conf

%files backend-mysql
%defattr(-,root,root,-)
%doc pdns/dnssec.schema.mysql.sql
%doc pdns/no-dnssec.schema.mysql.sql
%{_libdir}/%{name}/libgmysqlbackend.so

%files backend-postgresql
%defattr(-,root,root,-)
%{_libdir}/%{name}/libgpgsqlbackend.so
%doc pdns/dnssec.schema.pgsql.sql
%doc pdns/no-dnssec.schema.pgsql.sql

%files backend-pipe
%defattr(-,root,root,-)
%{_libdir}/%{name}/libpipebackend.so

%files backend-geo
%defattr(-,root,root,-)
%doc modules/geobackend/README
%{_libdir}/%{name}/libgeobackend.so

%files backend-ldap
%defattr(-,root,root,-)
%{_libdir}/%{name}/libldapbackend.so

%files backend-sqlite
%defattr(-,root,root,-)
%{_libdir}/%{name}/libgsqlite3backend.so
%doc pdns/dnssec.schema.sqlite3.sql
%doc pdns/no-dnssec.schema.sqlite3.sql
%doc pdns/bind-dnssec.schema.sqlite3.sql

%changelog
* Mon Apr 22 2013 Morten Stevens <mstevens@imt-systems.com> - 3.2-7
- Disarm dead code that causes gcc crashes on ARM (rhbz#954191)

* Tue Apr 09 2013 Morten Stevens <mstevens@imt-systems.com> - 3.2-6
- Add support for aarch64 (rhbz#926316)

* Tue Mar 05 2013 Ruben Kerkhof <ruben@rubenkerkhof.com> - 3.2-5
- Enable hardened build as per http://fedoraproject.org/wiki/Packaging:Guidelines#PIE

* Mon Feb 11 2013 Ruben Kerkhof <ruben@rubenkerkhof.com> - 3.2-4
- Enable PrivateTmp as per http://fedoraproject.org/wiki/Features/ServicesPrivateTmp
- Fix bogus date in changelog

* Sun Feb 10 2013 Denis Arnaud <denis.arnaud_fedora@m4x.org> - 3.2-3
- Rebuild for Boost-1.53.0

* Sat Feb 09 2013 Denis Arnaud <denis.arnaud_fedora@m4x.org> - 3.2-2
- Rebuild for Boost-1.53.0

* Thu Jan 17 2013 Morten Stevens <mstevens@imt-systems.com> - 3.2-1
- Update to 3.2

* Mon Jan 07 2013 Morten Stevens <mstevens@imt-systems.com> - 3.1-7
- Disable pdns guardian by default (rhbz#883852)
- Drop backend MongoDB as it does not work (upstream commit 3017)

* Thu Nov 22 2012 Ruben Kerkhof <ruben@rubenkerkhof.com> - 3.1-6
- Add example schemas to documentation

* Fri Oct 19 2012 Morten Stevens <mstevens@imt-systems.com> - 3.1-5
- Fixed permissions of pdns.conf file (rhbz#646510)
- Set bind as default backend

* Mon Sep 24 2012 Morten Stevens <mstevens@imt-systems.com> - 3.1-4
- use new systemd rpm macros (rhbz#850266)

* Mon Sep 24 2012 Morten Stevens <mstevens@imt-systems.com> - 3.1-3
- Fix pdns daemon exit code (rhbz#859898)
- Update systemd unit file

* Tue Sep 18 2012 Morten Stevens <mstevens@imt-systems.com> - 3.1-2
- Fix MongoDB backend

* Mon Sep 17 2012 Morten Stevens <mstevens@imt-systems.com> - 3.1-1
- Update to 3.1
- Remove MongoDB backend due build problems

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.0.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Feb 28 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.0.1-2
- Rebuilt for c++ ABI breakage

* Mon Jan 09 2012 Ruben Kerkhof <ruben@rubenkerkhof.com> 3.0.1-1
- CVE-2012-0206

* Sun Aug 07 2011 Dan Horák <dan@danny.cz> - 3.0-7
- mongodb supports only x86

* Mon Jul 25 2011 Ruben Kerkhof <ruben@rubenkerkhof.com> 3.0-6
- Upstream released new version

* Wed Jul 20 2011 Ruben Kerkhof <ruben@rubenkerkhof.com> 3.0-5.rc3
- New release candidate
- Add MongoDB backend
- Enable LUA support
- Convert to systemd

* Sat Apr 09 2011 Ruben Kerkhof <ruben@rubenkerkhof.com> 3.0-4.pre.20110327.2103.fc16
- Rebuilt for new boost

* Mon Mar 28 2011 Ruben Kerkhof <ruben@rubenkerkhof.com> 3.0-3.pre.20110327.2103
- License file moved a directory up
- Add pdnssec and dnsreplay commands

* Mon Mar 28 2011 Ruben Kerkhof <ruben@rubenkerkhof.com> 3.0-2.pre.20110327.2103
- Add lua BuildRequires

* Mon Mar 28 2011 Ruben Kerkhof <ruben@rubenkerkhof.com> 3.0-1.pre.20110327.2103
- Upstream released new pre-release version
- Now with DNSSEC support
- Drop merged patches

* Wed Mar 23 2011 Dan Horák <dan@danny.cz> - 2.9.22-13
- rebuilt for mysql 5.5.10 (soname bump in libmysqlclient)

* Wed Mar 23 2011 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.22-12
- Rebuilt for new mysqlclient

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.9.22-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Tue Dec 14 2010 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.22-10
- Fix crash on SIGSTOP and SIGCONT, thanks to Anders Kaseorg (#652841)

* Thu Jan 14 2010 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.22-9
- Fix changelog entry

* Thu Jan 14 2010 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.22-8
- Fix postgres lib detection (#555462)

* Fri Aug 21 2009 Tomas Mraz <tmraz@redhat.com> - 2.9.22-7
- rebuilt with new openssl

* Sat Jul 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.9.22-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu Feb 26 2009 Ruben Kerkhof <ruben@rubenkerkhof.com> - 2.9.22-5
- Fix build with gcc4.4

* Thu Feb 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.9.22-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Mon Jan 26 2009 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.22-3
- Upstream released new version

* Fri Jan 23 2009 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.22-2.rc3
- Rebuild for new libmysqlclient

* Mon Jan 19 2009 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.22-1.rc3
- New release candidate

* Wed Dec 03 2008 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.22-1.rc2
- Upstream released new release candidate
- Drop patches which are upstreamed

* Mon Nov 17 2008 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.21.2-1
- Upstream released new version

* Fri Sep 12 2008 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.21.1-2
- Fix handling of AAAA records (bz #461768)

* Wed Aug 06 2008 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.21.1-1
- CVE-2008-3337

* Sat Feb 09 2008 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.21-4
- GCC 4.3 fixes

* Wed Dec 05 2007 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.21-3
- Rebuild to pick up new openldap

* Tue Sep 11 2007 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.21-2
- Fix license tag
- Add README for geo backend to docs
* Tue Apr 24 2007 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.21-1
- Upstream released 2.9.21
- Enabled new SQLite backend
* Tue Apr 10 2007 <ruben@rubenkerkhof.com> 2.9.20-9
- Add Requires for chkconfig, service and useradd (#235582)
* Mon Jan 1 2007 <ruben@rubenkerkhof.com> 2.9.20-8
- Add the pdns user and group to the config file
- Don't restart pdns on an upgrade
- Minor cleanups in scriptlets
* Mon Jan 1 2007 <ruben@rubenkerkhof.com> 2.9.20-7
- Fixed typo in scriptlet
* Mon Jan 1 2007 <ruben@rubenkerkhof.com> 2.9.20-6
- Check if user pdns exists before adding it
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
