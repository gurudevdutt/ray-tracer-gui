"""OpticalSystem: ordered sequence of optical elements."""

from __future__ import annotations

from typing import List, Optional


from raytracergui.element import Element


class OpticalSystem:
    """An ordered sequence of optical elements along a common axis.

    Elements are stored in the order light encounters them. Spacings are
    *relative* to the previous element; absolute positions are the cumulative
    sum of spacings, with the first element measured from the ray origin at
    ``x = 0``.

    Parameters
    ----------
    elements : list of Element, optional
        Initial element list.  Defaults to an empty list.
    """

    def __init__(self, elements: Optional[List[Element]] = None) -> None:
        self._elements: List[Element] = list(elements) if elements is not None else []

    # ------------------------------------------------------------------
    # Sequence-like interface
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._elements)

    def __getitem__(self, index: int) -> Element:
        return self._elements[index]

    def __iter__(self):
        return iter(self._elements)

    def __repr__(self) -> str:  # pragma: no cover
        return f"OpticalSystem(elements={self._elements!r})"

    # ------------------------------------------------------------------
    # Position helpers
    # ------------------------------------------------------------------

    @property
    def absolute_positions(self) -> List[float]:
        """Absolute x-positions of each element, in millimetres.

        Returns
        -------
        list of float
            Cumulative sum of element spacings.  Empty list if no elements.
        """
        if not self._elements:
            return []
        spacings = [e.d for e in self._elements]
        pos = float(spacings[0])
        result = [pos]
        for s in spacings[1:]:
            pos += float(s)
            result.append(pos)
        return result

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def append(self, element: Element) -> None:
        """Append an element at the end of the system.

        Parameters
        ----------
        element : Element
            Element to append.
        """
        self._elements.append(element)

    def remove(self, index: int) -> Element:
        """Remove and return the element at *index*.

        Parameters
        ----------
        index : int
            Zero-based index of the element to remove.

        Returns
        -------
        Element
            The removed element.
        """
        return self._elements.pop(index)

    def insert(self, index: int, element: Element, strategy: str = "preserve") -> None:
        """Insert *element* before position *index*.

        Three spacing strategies are supported, matching the three MATLAB
        insertion modes:

        ``"preserve"``
            Halve the spacing of the existing element at *index*, giving half
            to the new element and keeping the other half on the shifted
            element.  Downstream spacings are unchanged.

        ``"add"``
            Insert the new element with its own ``element.d`` spacing intact;
            do not adjust any existing spacings.

        ``"front"``
            Insert at index 0 with the new element's own spacing; do not
            adjust any existing spacings.  Equivalent to ``strategy="add"``
            at index 0.

        Parameters
        ----------
        index : int
            Position before which the new element is inserted.
        element : Element
            Element to insert.
        strategy : str, optional
            One of ``"preserve"``, ``"add"``, or ``"front"``.
            Defaults to ``"preserve"``.
        """
        if strategy == "preserve":
            if 0 <= index < len(self._elements):
                original_d = self._elements[index].d
                half = original_d / 2.0
                # new element gets the first half
                element = Element(
                    d=half,
                    f=element.f,
                    diameter=element.diameter,
                    on=element.on,
                    name=element.name,
                )
                # existing element keeps the second half
                old = self._elements[index]
                self._elements[index] = Element(
                    d=half,
                    f=old.f,
                    diameter=old.diameter,
                    on=old.on,
                    name=old.name,
                )
            self._elements.insert(index, element)
        elif strategy in ("add", "front"):
            self._elements.insert(index, element)
        else:
            raise ValueError(f"Unknown insertion strategy: {strategy!r}")
