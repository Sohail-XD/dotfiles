const resource = file => `resource:///com/github/Aylur/ags/${file}.js`;
const require = async file => (await import(resource(file))).default;
const service = async file => (await require(`service/${file}`)).instance;

export const App = await require('app');
App.connect = (...args) => App.instance.connect(...args);

export const Widget = await require('widget');
export const Service = await require('service');
export const Variable = await require('variable');
export const Utils = await import(resource('utils'));
export const Hyprland = await service('hyprland');
