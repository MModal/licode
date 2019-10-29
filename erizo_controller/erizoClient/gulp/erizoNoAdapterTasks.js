const erizoNoAdapterTasks = (gulp, plugins, config) => {
  const that = {};
  if (!config.paths) {
    return;
  }
  const erizoConfig = {
    entry: `${config.paths.entry}ErizoNoAdapter.js`,
    webpackConfig: require('../webpack.config.erizonoadapter.js'),
    debug: `${config.paths.debug}/erizonoadapter`,
    production: `${config.paths.production}/erizonoadapter`,
  };

  that.bundle = () =>
    gulp.src(erizoConfig.entry, { base: './' })
    .pipe(plugins.webpackGulp(erizoConfig.webpackConfig, plugins.webpack))
    .on('error', anError => console.log('An error ', anError))
    .pipe(gulp.dest(erizoConfig.debug))
    .on('error', anError => console.log('An error ', anError));

  that.compile = () =>
    gulp.src(`${erizoConfig.debug}/**/*.js`, { base: './' })
      .pipe(plugins.sourcemaps.init())
      .pipe(plugins.closureCompiler({
        languageIn: 'ECMASCRIPT6',
        languageOut: 'ECMASCRIPT5',
        jsOutputFile: 'erizo.js',
        createSourceMap: true,
      }))
      .pipe(plugins.sourcemaps.write('/')) // gulp-sourcemaps automatically adds the sourcemap url comment
      .pipe(gulp.dest(erizoConfig.production));

  that.dist = () =>
    gulp.src(`${erizoConfig.production}/**/*.js*`)
    .pipe(gulp.dest(config.paths.basicExample));

  that.clean = () =>
    plugins.del([`${erizoConfig.debug}/**/*.js*`, `${erizoConfig.production}/**/*.js*`],
    { force: true });

  return that;
};

module.exports = erizoNoAdapterTasks;
