Name:		nfs-utils
Epoch:		1
Version:	1.1.3
Release:	%mkrel 4
Summary:	The utilities for Linux NFS server
Group:		Networking/Other
License:	GPL
URL:		http://sourceforge.net/projects/nfs/
Source0:	http://prdownloads.sourceforge.net/nfs/%{name}-%{version}.tar.gz
Source1:	ftp://nfs.sourceforge.net/pub/nfs/nfs.doc.tar.bz2
Source2:	nfs-common.init
Source3:	nfs-server.init
Source4:	nfs-common.sysconfig
Source5:	nfs-server.sysconfig
Source8:	nfsv4.schema
Source9:	gssapi_mech.conf
Source10:	idmapd.conf
Source11: 	bash-completion
Patch3:		nfs-utils-1.1.0-perms.patch
Patch52:	nfs-utils-1.0.6-idmap.conf.patch
Requires:	nfs-utils-clients = %{version}-%{release}
# needed because of /etc/exports transfer
Conflicts:	setup < 2.7.8
Conflicts:	clusternfs
Requires(post): rpm-helper
Requires(preun): rpm-helper
Requires:	    tcp_wrappers
BuildRequires:	krb5-devel >= 1.3
BuildRequires:	libevent-devel
BuildRequires:	nfsidmap-devel >= 0.16
BuildRequires:	rpcsecgss-devel >= 0.12
BuildRequires:	tcp_wrappers-devel
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
The nfs-utils package provides a daemon for the kernel NFS server
and related tools, which provides a much higher level of
performance than the traditional Linux NFS server used by most
users.

This package also contains the showmount program. Showmount
queries the mount daemon on a remote host for information about
the NFS (Network File System) server on the remote host. For
example, showmount can display the clients which are mounted on
that host.

%package	clients
Summary:	The utilities for Linux NFS client
Group:		Networking/Other
Requires:	portmapper
# needed because of service scripts and rpcdebug/nfsstat transfer
Conflicts:  nfs-utils < 1.1.2-3mdv
Requires(pre): rpm-helper
Requires(post): rpm-helper
Requires(preun): rpm-helper
Requires(postun): rpm-helper

%description	clients
The nfs-utils package provides a daemon for the kernel NFS server
and related tools, which provides a much higher level of
performance than the traditional Linux NFS server used by most
users.

This package also contains the showmount program. Showmount
queries the mount daemon on a remote host for information about
the NFS (Network File System) server on the remote host. For
example, showmount can display the clients which are mounted on
that host.

%prep
%setup -q -a1 -n %{name}-%{version}

# fix strange perms
find . -type d -perm 0700 -exec chmod 755 {} \;
find . -type f -perm 0555 -exec chmod 755 {} \;
find . -type f -perm 0444 -exec chmod 644 {} \;

%patch3 -p1 -b .perms
%patch52 -p1 -b .conf

cp %{SOURCE8} nfsv4.schema

%build
autoreconf
%serverbuild
%configure2_5x \
    --with-statedir=%{_localstatedir}/lib/nfs \
    --with-statduser=rpcuser \
    --enable-nfsv3 \
    --enable-nfsv4 \
    --enable-gss \
    --enable-secure-statd \
    --with-krb5=%{_prefix} \
    --disable-rquotad

make all

%install
rm -rf %{buildroot}

install -d %{buildroot}{/sbin,/usr/sbin}
install -d %{buildroot}%{_mandir}/{man5,man8}
install -d %{buildroot}%{_initrddir}
install -d %{buildroot}%{_sysconfdir}/sysconfig
install -d %{buildroot}%{_localstatedir}/lib/nfs/statd
install -d %{buildroot}%{_localstatedir}/lib/nfs/v4recovery
install -d %{buildroot}%{_localstatedir}/lib/nfs/sm

%make \
	DESTDIR=%{buildroot} \
	MANDIR=%{buildroot}%{_mandir} \
	SBINDIR=%{buildroot}%{_prefix}/sbin \
	install

install -m0755 tools/rpcdebug/rpcdebug %{buildroot}/sbin/
ln -snf rpcdebug %{buildroot}/sbin/nfsdebug
ln -snf rpcdebug %{buildroot}/sbin/nfsddebug

install -m 755 %{SOURCE2} %{buildroot}%{_initrddir}/nfs-common
install -m 755 %{SOURCE3} %{buildroot}%{_initrddir}/nfs-server
install -m 644 %{SOURCE4} %{buildroot}%{_sysconfdir}/sysconfig/nfs-common
install -m 644 %{SOURCE5} %{buildroot}%{_sysconfdir}/sysconfig/nfs-server

touch %{buildroot}%{_localstatedir}/lib/nfs/rmtab
mv %{buildroot}%{_sbindir}/rpc.statd %{buildroot}/sbin/

install -m 644 %{SOURCE10} %{buildroot}%{_sysconfdir}/idmapd.conf
install -m 644 %{SOURCE9} %{buildroot}%{_sysconfdir}/gssapi_mech.conf
perl -pi -e "s|/usr/lib|%{_libdir}|g" %{buildroot}%{_sysconfdir}/gssapi_mech.conf
install -d %{buildroot}%{_localstatedir}/lib/nfs/rpc_pipefs

# nuke dupes
rm -f %{buildroot}%{_sbindir}/rpcdebug

cat >%{buildroot}%{_sysconfdir}/exports <<EOF
# /etc/exports: the access control list for filesystems which may be exported
#               to NFS clients.  See exports(5).
EOF

cat >README.1.1.0.upgrade.urpmi <<EOF
This release changed organisation of init scripts:
- rpcidmapd, rpcgssd and nfslock have been merged in nfs-common
- rpcsvcgssd and nfs have been merged in nfs-server
Individual daemons handled previously by those init scripts are now handled
automatically, according to current nfs configuration and to init scripts
configuration files /etc/sysconfig/nfs-common and /etc/sysconfig/nfs-server.
EOF

# manage documentation manually
install -d -m 755 %{buildroot}%{_docdir}/%{name}
install -m 644 README README.1.1.0.upgrade.urpmi ChangeLog COPYING NEWS \
               nfs/*.html nfs/*.ps nfsv4.schema \
               %{buildroot}%{_docdir}/%{name}

# bash completion
install -d -m 755 %{buildroot}%{_sysconfdir}/bash_completion.d
install -m 644 %{SOURCE11} %{buildroot}%{_sysconfdir}/bash_completion.d/%{name}

%post
%_post_service nfs-server
if [ $1 = 2 ]; then
    # handle upgrade from previous init script scheme
    if [ -f %{_initrddir}/nfs ]; then
        # map activation status of old script
        if [ `LC_ALL=C chkconfig --list nfs | cut -f 5` == '3:on' ]; then
            chkconfig --add nfs-server
        fi
        # don't leave dangling symlinks
        chkconfig --del nfs
    fi
    [ -f %{_initrddir}/rpcsvcgssd ] && chkconfig --del rpcsvcgssd
    # always finish with a true status, otherwise rpm barks
    /bin/true
fi

%create_ghostfile %{_localstatedir}/lib/nfs/xtab root root 644
%create_ghostfile %{_localstatedir}/lib/nfs/etab root root 644
%create_ghostfile %{_localstatedir}/lib/nfs/rmtab root root 644

%preun
%_preun_service nfs-server

%pre clients
%_pre_useradd rpcuser %{_localstatedir}/lib/nfs /bin/false

%post clients
%_post_service nfs-common
# restart nfs-server service if running
if [ -f /var/lock/subsys/nfs-server ]; then
    /sbin/service nfs-server restart > /dev/null 2>&1 ||
fi
if [ $1 = 2 ]; then
    # handle upgrade from previous init script scheme
    if [ -f %{_initrddir}/nfslock ]; then
        # map activation status of old script
        if [ `LC_ALL=C chkconfig --list nfslock | cut -f 5` == '3:on' ]; then
            chkconfig --add nfs-common
        fi
        # don't leave dangling symlinks
        chkconfig --del nfslock
    fi
    [ -f %{_initrddir}/rpcgssd ]   && chkconfig --del rpcgssd
    [ -f %{_initrddir}/rpcidmapd ] && chkconfig --del rpcidmapd
    # always finish with a true status, otherwise rpm barks
    /bin/true
fi

%preun clients
%_preun_service nfs-common

%postun clients
%_postun_userdel rpcuser

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%{_docdir}/%{name}/*
%exclude %{_docdir}/%{name}/README*
%{_initrddir}/nfs-server
%config(noreplace) %{_sysconfdir}/sysconfig/nfs-server
%config(noreplace) %ghost %{_localstatedir}/lib/nfs/xtab
%config(noreplace) %ghost %{_localstatedir}/lib/nfs/etab
%config(noreplace) %ghost %{_localstatedir}/lib/nfs/rmtab
%config(noreplace) %{_sysconfdir}/exports
/sbin/nfsddebug
%{_sbindir}/exportfs
%{_sbindir}/rpc.mountd
%{_sbindir}/rpc.nfsd
%{_sbindir}/rpc.svcgssd
%{_mandir}/man5/exports.5*
%{_mandir}/man7/nfsd.7*
%{_mandir}/man8/exportfs.8*
%{_mandir}/man8/mountd.8*
%{_mandir}/man8/nfsd.8*
%{_mandir}/man8/rpc.mountd.8*
%{_mandir}/man8/rpc.nfsd.8*
%{_mandir}/man8/rpc.svcgssd.8*
%{_mandir}/man8/svcgssd.8*

%files clients
%defattr(-,root,root)
%dir %{_docdir}/%{name}
%{_docdir}/%{name}/README*
%{_sysconfdir}/bash_completion.d/%{name}
%config(noreplace) %{_sysconfdir}/sysconfig/nfs-common
%{_initrddir}/nfs-common
/sbin/rpc.statd
/sbin/mount.nfs
/sbin/mount.nfs4
/sbin/umount.nfs
/sbin/umount.nfs4
/sbin/rpcdebug
/sbin/nfsdebug
%{_sbindir}/sm-notify
%{_sbindir}/start-statd
%{_sbindir}/showmount
%{_mandir}/man5/nfs.5*
%{_mandir}/man8/mount.nfs.8*
%{_mandir}/man8/rpc.sm-notify.8*
%{_mandir}/man8/sm-notify.8*
%{_mandir}/man8/umount.nfs.8*
%{_mandir}/man8/rpc.statd.8*
%{_mandir}/man8/statd.8*
%{_mandir}/man8/showmount.8*
%{_mandir}/man8/nfsstat.8*
%{_mandir}/man8/rpcdebug.8*
%dir %{_localstatedir}/lib/nfs
%dir %{_localstatedir}/lib/nfs/v4recovery
%dir %{_localstatedir}/lib/nfs/state
%dir %attr(0700,rpcuser,rpcuser) %{_localstatedir}/lib/nfs/sm
%dir %attr(0700,rpcuser,rpcuser) %{_localstatedir}/lib/nfs/statd
%config(noreplace) %{_sysconfdir}/idmapd.conf
%config(noreplace) %{_sysconfdir}/gssapi_mech.conf
%dir %{_localstatedir}/lib/nfs/rpc_pipefs
%{_sbindir}/nfsstat
%{_sbindir}/rpc.idmapd
%{_sbindir}/rpc.gssd
%{_sbindir}/gss_clnt_send_err
%{_sbindir}/gss_destroy_creds
%{_mandir}/man5/idmapd.conf.5*
%{_mandir}/man8/rpc.gssd.8*
%{_mandir}/man8/rpc.idmapd.8*
%{_mandir}/man8/gssd.8*
%{_mandir}/man8/idmapd.8*
