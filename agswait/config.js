import Overview from './js/overview/Overview.js';

setup.scssWatcher();
setup.globalServices();

export default {
    windows: [
        Overview(),
    ].flat(2),
};
