%global backends %{nil}
%global commit de6d565b6f2ad4872fc97ade000b43357492ba25
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Name: pdns
Version: 3.4.0
Release: 0.2.%{shortcommit}%{?dist}
Summary: A modern, advanced and high performance authoritative-only nameserver
Group: System Environment/Daemons
License: GPLv2
URL: http://powerdns.com
Source0: https://github.com/Powerdns/pdns/archive/%{commit}/pdns-%{commit}.tar.gz
Patch0: pdns-fixinit.patch

Requires(pre): shadow-utils
Requires(post): /sbin/chkconfig
Requires(preun): /sbin/service, /sbin/chkconfig
Requires(postun): /sbin/service

BuildRequires: boost-devel
BuildRequires: lua-devel
BuildRequires: cryptopp-devel
BuildRequires: bison
BuildRequires: polarssl-devel
BuildRequires: libtool
BuildRequires: ragel
BuildRequires: flex
BuildRequires: asciidoc
BuildRequires: xmlto
BuildRequires: p11-kit-devel
BuildRequires: zeromq-devel

%description
The PowerDNS Nameserver is a modern, advanced and high performance
authoritative-only nameserver. It is written from scratch and conforms
to all relevant DNS standards documents.
Furthermore, PowerDNS interfaces with almost any database.

%package tools
Summary: Extra tools for %{name}
Group: System Environment/Daemons

%description tools
This package contains the extra tools for %{name}

%package backend-mysql
Summary: MySQL backend for %{name}
Group: System Environment/Daemons
Requires: %{name}%{?_isa} = %{version}-%{release}
BuildRequires: mysql-devel
%global backends %{backends} gmysql

%description backend-mysql
This package contains the gmysql backend for %{name}

%package backend-postgresql
Summary: PostgreSQL backend for %{name}
Group: System Environment/Daemons
Requires: %{name}%{?_isa} = %{version}-%{release}
BuildRequires: postgresql-devel
%global backends %{backends} gpgsql

%description backend-postgresql
This package contains the gpgsql backend for %{name}

%package backend-pipe
Summary: Pipe backend for %{name}
Group: System Environment/Daemons
Requires: %{name}%{?_isa} = %{version}-%{release}
%global backends %{backends} pipe

%description backend-pipe
This package contains the pipe backend for %{name}

%package backend-remote
Summary: Remote backend for %{name}
Group: System Environment/Daemons
Requires: %{name}%{?_isa} = %{version}-%{release}
BuildRequires: libcurl-devel
%global backends %{backends} remote

%description backend-remote
This package contains the remote backend for %{name}

%package backend-geo
Summary: Geo backend for %{name}
Group: System Environment/Daemons
Requires: %{name}%{?_isa} = %{version}-%{release}
%global backends %{backends} geo

%description backend-geo
This package contains the geo backend for %{name}
It allows different answers to DNS queries coming from different
IP address ranges or based on the geographic location

%package backend-ldap
Summary: LDAP backend for %{name}
Group: System Environment/Daemons
Requires: %{name}%{?_isa} = %{version}-%{release}
BuildRequires: openldap-devel
%global backends %{backends} ldap

%description backend-ldap
This package contains the ldap backend for %{name}

%package backend-lua
Summary: LUA backend for %{name}
Group: System Environment/Daemons
Requires: %{name}%{?_isa} = %{version}-%{release}
%global backends %{backends} lua

%description backend-lua
This package contains the lua backend for %{name}

%package backend-sqlite
Summary: SQLite backend for %{name}
Group: System Environment/Daemons
Requires: %{name}%{?_isa} = %{version}-%{release}
BuildRequires: sqlite-devel
%global backends %{backends} gsqlite3

%description backend-sqlite
This package contains the SQLite backend for %{name}

%prep
%setup -qn %{name}-%{commit}
%patch0 -p1 -b .fixinit

sed -i 's/^# launch=/launch=bind/' pdns/pdns.conf-dist
sed -i 's/^# setuid=/setuid=pdns/' pdns/pdns.conf-dist
sed -i 's/^# setgid=/setgid=pdns/' pdns/pdns.conf-dist

# No inclusion of pre-built binaries or libraries
rm -rf pdns/ext/polarssl-*

%build
export CPPFLAGS="-DLDAP_DEPRECATED"
./bootstrap
%configure \
	--sysconfdir=%{_sysconfdir}/%{name} \
	--disable-static \
	--with-modules='' \
        --with-system-polarssl \
	--with-lua \
	--with-dynmodules='%{backends}' \
	--enable-cryptopp \
	--enable-tools \
	--enable-remotebackend-zeromq \
	--enable-experimental-pkcs11

sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

make %{?_smp_mflags}

%install
make install DESTDIR=%{buildroot}

%{__rm} -f %{buildroot}%{_libdir}/%{name}/*.la
%{__install} -p -D -m 0755 pdns/pdns %{buildroot}%{_initrddir}/pdns
%{__mv} %{buildroot}%{_sysconfdir}/%{name}/pdns.conf{-dist,}

chmod 600 %{buildroot}%{_sysconfdir}/%{name}/pdns.conf

%pre
getent group pdns >/dev/null || groupadd -r pdns
getent passwd pdns >/dev/null || \
	useradd -r -g pdns -d / -s /sbin/nologin \
	-c "PowerDNS user" pdns
exit 0

%post
/sbin/chkconfig --add pdns

%preun
if [ $1 -eq 0 ]; then
	/sbin/service pdns stop >/dev/null 2>&1 || :
	/sbin/chkconfig --del pdns
fi

%postun
if [ $1 -ge 1 ]; then
	/sbin/service pdns condrestart >/dev/null 2>&1 || :
fi

%files
%doc COPYING README
%{_bindir}/pdns_control
%{_bindir}/pdnssec
%{_bindir}/zone2ldap
%{_bindir}/zone2sql
%{_bindir}/zone2json
%{_sbindir}/pdns_server
%{_mandir}/man8/pdns_control.8.gz
%{_mandir}/man8/pdns_server.8.gz
%{_mandir}/man8/zone2sql.8.gz
%{_mandir}/man8/zone2ldap.8.gz
%{_mandir}/man8/pdnssec.8.gz
%{_initrddir}/pdns
%dir %{_libdir}/%{name}/
%dir %{_sysconfdir}/%{name}/
%config(noreplace) %{_sysconfdir}/%{name}/pdns.conf

%files tools
%{_bindir}/dnsbulktest
%{_bindir}/dnsdist
%{_bindir}/dnsreplay
%{_bindir}/dnsscan
%{_bindir}/dnsscope
%{_bindir}/dnstcpbench
%{_bindir}/dnswasher
%{_bindir}/nproxy
%{_bindir}/nsec3dig
%{_bindir}/saxfr
%{_mandir}/man8/dnsreplay.8.gz
%{_mandir}/man8/dnsscope.8.gz
%{_mandir}/man8/dnswasher.8.gz
%{_mandir}/man1/dnstcpbench.1.gz

%files backend-mysql
%doc modules/gmysqlbackend/dnssec-3.x_to_3.4.0_schema.mysql.sql
%doc modules/gmysqlbackend/nodnssec-3.x_to_3.4.0_schema.mysql.sql
%doc modules/gmysqlbackend/schema.mysql.sql
%{_libdir}/%{name}/libgmysqlbackend.so

%files backend-postgresql
%doc modules/gpgsqlbackend/dnssec-3.x_to_3.4.0_schema.pgsql.sql
%doc modules/gpgsqlbackend/nodnssec-3.x_to_3.4.0_schema.pgsql.sql
%doc modules/gpgsqlbackend/schema.pgsql.sql
%{_libdir}/%{name}/libgpgsqlbackend.so

%files backend-pipe
%{_libdir}/%{name}/libpipebackend.so

%files backend-remote
%{_libdir}/%{name}/libremotebackend.so

%files backend-geo
%doc modules/geobackend/README
%{_libdir}/%{name}/libgeobackend.so

%files backend-ldap
%{_libdir}/%{name}/libldapbackend.so

%files backend-lua
%{_libdir}/%{name}/libluabackend.so

%files backend-sqlite
%doc modules/gsqlite3backend/dnssec-3.x_to_3.4.0_schema.sqlite3.sql
%doc modules/gsqlite3backend/nodnssec-3.x_to_3.4.0_schema.sqlite3.sql
%doc modules/gsqlite3backend/schema.sqlite3.sql
%{_libdir}/%{name}/libgsqlite3backend.so

%changelog
* Wed Jul 16 2014 Ruben Kerkhof <ruben@tilaa.com> 3.4.0-0.2.de6d565
- Enable zeromq remote backend
- Enable experimental PKCS11 support

* Tue Jul 15 2014 Ruben Kerkhof <ruben@tilaa.com> 3.4.0-0.1.de6d565
- Upgrade to de6d565b6f2a for various
  remotebackend fixes

* Tue Dec 17 2013 Morten Stevens <mstevens@imt-systems.com> - 3.3.1-1
- Update to latest upstream release 3.3.1
- Some more DNSSEC improvements
- Several bugs fixed since 3.1
- Add extra tools package for pdns
- Add Remote backend
- Add LUA backend
- Enable remotebackend-http
- Add extra tools package for pdns
- Add polarssl-devel as build dependency
- Fix bogus date in changelog

* Sun Oct 28 2012 Morten Stevens <mstevens@imt-systems.com> - 3.1-2
- Spec improvements

* Fri Oct 26 2012 Morten Stevens <mstevens@imt-systems.com> - 3.1-1
- Update to latest upstream release 3.1
- DNSSEC improvements
- several bugs fixed since 2.9.22
- Added condrestart option

* Sat Oct 20 2012 Morten Stevens <mstevens@imt-systems.com> - 2.9.22.6-2
- Fixed permissions of pdns.conf file (rhbz#646510)
- Set bind as default backend

* Wed Feb 01 2012 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.22.6-1
- Upstream released new version. Fixes crash introduced in 2.9.22.5

* Mon Jan 09 2012 Ruben Kerkhof <ruben@rubenkerkhof.com> 2.9.22.5-1
- CVE-2012-0206

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
