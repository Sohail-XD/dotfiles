import Overview from './js/overview/Overview.js';
import Applauncher from './js/applauncher/Applauncher.js';
import options from './js/options.js';
import * as setup from './js/utils.js';
import { forMonitors } from './js/utils.js';

setup.globalServices();

export default {
    maxStreamVolume: 1.05,
    windows: [
        Applauncher(),
        Overview(),
    ].flat(2),
};
