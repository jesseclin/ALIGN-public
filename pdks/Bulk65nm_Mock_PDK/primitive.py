from align.primitive import default

class MOSGenerator(default.MOSGenerator):

    def _addMOS( self, x, y, x_cells, vt_type, name='M1', reflect=False, **parameters):

        # Draw default layers
        super()._addMOS(x, y, x_cells, vt_type, name, reflect, **parameters) 
        def _addRVT(x, y, x_cells):
            if self.shared_diff == 0:
                self.addWire( self.RVT,  None, None, y,          (x, 1), (x+1, -1))
            elif self.shared_diff == 1 and x == x_cells-1:
                self.addWire( self.RVT_diff,  None, None, y, 0, 2*x_cells+1)
            else:
                pass
    
        def _addLVT(x, y, x_cells):
            if self.shared_diff == 0:
                self.addWire( self.LVT,  None, None, y,          (x, 1), (x+1, -1))
            elif self.shared_diff == 1 and x == x_cells-1:
                self.addWire( self.LVT_diff,  None, None, y, 0, 2*x_cells+1)
            else:
                pass
    
        def _addHVT(x, y, x_cells):
            if self.shared_diff == 0:
                self.addWire( self.HVT,  None, None, y,          (x, 1), (x+1, -1))
            elif self.shared_diff == 1 and x == x_cells-1:
                self.addWire( self.HVT_diff,  None, None, y, 0, 2*x_cells+1)
            else:
                pass
        add_vt = '_add' + vt_type
        eval(add_vt)(x, y, x_cells)

#
# Default Cap & Res generators are good enough
#

CapGenerator = default.CapGenerator
ResGenerator = default.ResGenerator

