%global with_python3 1

%if 0%{?fedora} && 0%{?fedora} <= 12
%global with_python3 0
%endif

%if 0%{?rhel} && 0%{?rhel} <= 7
%global with_python3 0
%endif


# compatibility with older releases
%{!?__python2: %global __python2 /usr/bin/python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%{!?py2_build: %global py2_build %{expand: CFLAGS="%{optflags}" %{__python2} setup.py %{?py_setup_args} build --executable="%{__python2} -s"}}
%{!?py2_install: %global py2_install %{expand: CFLAGS="%{optflags}" %{__python2} setup.py %{?py_setup_args} install -O1 --skip-build --root %{buildroot}}}


Name:           releng-sop
Version:        0.1
Release:        1%{?dist}
Summary:        Release Engineering Standard Operating Procedures

Group:          Development/Tools
License:        MIT
URL:            https://github.com/release-engineering/releng-sop.git
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:       koji
Requires:       python2-%{name}

BuildRequires:  python2-devel
#BuildRequires:  python2-sphinx_rtd_theme
BuildRequires:  python-setuptools
BuildRequires:  python-six

%if  0%{?with_python3}
BuildRequires:  python3-devel
#BuildRequires:  python3-sphinx_rtd_theme
BuildRequires:  python3-setuptools
BuildRequires:  python3-six
%endif


%description
Release Engineering Standard Operating Procedures


%package -n python2-%{name}
Summary:        Python 2 modules for %{name}
Group:          Development/Tools
Requires:       %{name}
Requires:       python2-productmd
Requires:       pyxdg
Requires:       python2-releng-sop
Requires:       python-six

%description -n python2-%{name}
Python 2 modules for %{name}


%if 0%{?with_python3}
%package -n python3-%{name}
Summary:        Python 3 modules for %{name}
Group:          Development/Tools
Requires:       %{name}
Requires:       python3-productmd
Requires:       python3-pyxdg
Requires:       python3-releng-sop
Requires:       python3-six

%description -n python3-%{name}
Python 3 modules for %{name}
%endif


%prep
%setup -n %{name}-%{version}


%build
%py2_build

%if 0%{with_python3}
%py3_build
%endif


%install
# Scripts in /usr/bin are overwritten with every setup.py install.
# We want python2 versions because koji doesn't support python3 yet.
%if 0%{with_python3}
%py3_install
%endif

%py2_install


%check
#%{__python2} setup.py test

%if 0%{with_python3}
#%{__python3} setup.py test
%endif


%files
/usr/bin/*

%files -n python2-%{name}
%{python2_sitelib}/releng_sop/
%{python2_sitelib}/releng_sop-%{version}-py?.?.egg-info


%if 0%{?with_python3}
%files -n python3-%{name}
%{python3_sitelib}/releng_sop/
%{python3_sitelib}/releng_sop-%{version}-py?.?.egg-info
%endif


%changelog
* Tue Dec 13 2016 Daniel Mach <dmach@redhat.com> - 0.1-1
- Initial package
