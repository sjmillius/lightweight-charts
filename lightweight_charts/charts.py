"""Experimental simple wrapper for tradingview's lightweight-charts."""

import dataclasses
import itertools
import jinja2
import json
import pandas as pd
import uuid

from typing import List, Dict

_TEMPLATE = jinja2.Template("""
   <script src="{{ base_url }}lightweight-charts.standalone.production.js"></script> 
   
   <div id="{{ output_div }}"></div>
   <script type="text/javascript">
     (() => {
     const outputDiv = document.getElementById("{{ output_div }}");
     const chart = LightweightCharts.createChart(outputDiv, {{ chart.options }});

     {% for series in chart.series %}
     (() => {
       const chart_series = chart.add{{ series.series_type }}Series(
         {{ series.options }}
       );
       chart_series.setData(
         {{ series.data }}
       );
       chart_series.setMarkers(
         {{ series.markers }}
       );
       {% for price_line in series.price_lines %}
       chart_series.createPriceLine({{ price_line }});
       {% endfor %}
     })();
     {% endfor %}
     })();
   </script>
""")


# Model specification.
@dataclasses.dataclass
class _SeriesSpec:
  series_type: str
  data: str
  options: str
  price_lines: List[Dict]
  markers: str


@dataclasses.dataclass
class _ChartSpec:
  options: str
  series: List[_SeriesSpec]


def _render(chart: _ChartSpec,
            base_url: str = "https://unpkg.com/lightweight-charts/dist/",
            output_div: str = "vis") -> str:
  """Render a model as html for viewing."""
  return _TEMPLATE.render(chart=chart, base_url=base_url, output_div=output_div)


def _encode(data: pd.DataFrame, **kwargs) -> pd.DataFrame:
  """Rename and select columns from a data frame."""
  return data.rename(columns={value: key for key, value in kwargs.items()})[[
      *kwargs.keys()
  ]]


class _Markers:
  """Series markers."""

  def __init__(self, chart, data: pd.DataFrame, **kwargs):
    self._chart = chart
    self._data = data
    self.options = kwargs

  def encode(self, **kwargs):
    self._data = _encode(self._data, **kwargs)

  def _spec(self):
    return [{
        **self.options,
        **marker
    } for marker in self._data.to_dict(orient='records', date_format='iso')]

  def _repr_html_(self):
    return self._chart._repr_html_()


class Series:

  def __init__(self, chart, data: pd.DataFrame, series_type: str, **kwargs):
    self._chart = chart
    self.series_type = series_type
    self._data = data
    self.options = kwargs
    self._price_lines = []
    self._single_markers = []
    self._markers = []

  def encode(self, **kwargs):
    self._data = _encode(self._data, **kwargs)
    return self

  def price_line(self, **kwargs):
    self._price_lines.append(kwargs)
    return self

  def annotation(self, **kwargs):
    self._single_markers.append(kwargs)
    return self

  def mark_annotation(self, data: pd.DataFrame = None, **kwargs) -> _Markers:
    markers = _Markers(chart=self._chart,
                       data=data if data is not None else self._data,
                       **kwargs)
    self.markers.append(markers)
    return markers

  def _spec(self) -> _SeriesSpec:
    return _SeriesSpec(
        series_type=self.series_type,
        data=self._data.to_json(orient='records', date_format='iso'),
        options=json.dumps(self.options),
        price_lines=self._price_lines,
        markers=json.dumps(self._single_markers + list(
            itertools.chain(*[marker._spec() for marker in self._markers]))))

  def _repr_html_(self):
    return self._chart._repr_html_()


class Chart:
  """A lightweight chart."""

  def __init__(self,
               data: pd.DataFrame = None,
               width: int = 400,
               height: int = 300,
               **kwargs):
    self.width = width
    self.height = height
    self.options = kwargs
    self.series = []
    self._data = data

  def add(self, series: Series):
    self.series.append(series)
    return series

  def mark_line(self, data: pd.DataFrame = None, **kwargs) -> Series:
    """Add a line series."""
    return self.add(
        Series(chart=self,
               series_type='Line',
               data=data if data is not None else self._data,
               **kwargs))

  def mark_area(self, data: pd.DataFrame = None, **kwargs) -> Series:
    """Add an area series."""
    return self.add(
        Series(chart=self,
               series_type='Area',
               data=data if data is not None else self._data,
               **kwargs))

  def mark_bar(self, data: pd.DataFrame = None, **kwargs) -> Series:
    """Add a bar series."""
    return self.add(
        Series(chart=self,
               series_type='Bar',
               data=data if data is not None else self._data,
               **kwargs))

  def mark_candlestick(self, data: pd.DataFrame = None, **kwargs) -> Series:
    """Add a candlestick series."""
    return self.add(
        Series(chart=self,
               series_type='Candlestick',
               data=data if data is not None else self._data,
               **kwargs))

  def mark_histogram(self, data: pd.DataFrame = None, **kwargs) -> Series:
    """Add a histogram series."""
    return self.add(
        Series(chart=self,
               series_type='Histogram',
               data=data if data is not None else self._data,
               **kwargs))

  def _spec(self) -> _ChartSpec:
    options = {'width': self.width, 'height': self.height, **self.options}
    return _ChartSpec(options=options,
                      series=[series._spec() for series in self.series])

  def _repr_html_(self):
    return _render(self._spec(), output_div=f'vis-{uuid.uuid4().hex}')