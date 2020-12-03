module.exports = {
  showElevation: showElevation,
  generateLatLong: generateLatLong
}

function getRandomInRange(from, to, fixed) {
    return (Math.random() * (to - from) + from).toFixed(fixed) * 1;
    // .toFixed() returns string, so ' * 1' is a trick to convert to number
}

function generateLatLong(userContext, events, done) {

  userContext.vars.latitude = getRandomInRange(-90, 90, 3);
  userContext.vars.longitude = getRandomInRange(-180, 180, 3);
  console.log("\nLat:" + userContext.vars.latitude);
  // console.log("\nLon:" + userContext.vars.longitude);  
  return done(); // MUST be called for the scenario to continue
}

function showElevation(requestParams, response, context, ee, next) {
  // console.log("\nResponse:\n" + response.body);
  console.log("\nElevation:\n" + context.vars.elevation);
  return next(); // MUST be called for the scenario to continue
}
