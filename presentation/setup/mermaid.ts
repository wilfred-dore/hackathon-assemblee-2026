import { defineMermaidSetup } from '@slidev/types'

export default defineMermaidSetup(() => ({
  theme: 'base',
  themeVariables: {
    fontFamily: 'Inter, sans-serif',
    fontSize: '15px',
    primaryColor: '#131f3d',
    primaryTextColor: '#eef2fb',
    primaryBorderColor: '#5b8cff',
    secondaryColor: '#182543',
    tertiaryColor: '#0e1730',
    lineColor: '#a8c0ff',
    edgeLabelBackground: '#0e1730',
    clusterBkg: '#0e1730',
    nodeTextColor: '#eef2fb',
  },
}))
