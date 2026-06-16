'use client'

// Plotly needs the browser, so this module is only ever loaded client-side
// (via next/dynamic with ssr:false in the page). Using the factory + the
// prebuilt dist bundle avoids bundling plotly.js from source under webpack.
import createPlotlyComponent from 'react-plotly.js/factory'
import Plotly from 'plotly.js-dist-min'

const Plot = createPlotlyComponent(Plotly)

export default Plot
