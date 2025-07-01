import openmdao.api as om


class OpenLoopControllerBaseClass(om.ExplicitComponent):
    def initialize(self):
        self.options.declare("plant_config", types=dict)
        self.options.declare("tech_config", types=dict)

    def setup(self):
        resource_name = self.options["tech_config"]["model_inputs"]["shared_parameters"][
            "resource_name"
        ]
        resource_units = self.options["tech_config"]["model_inputs"]["shared_parameters"][
            "resource_units"
        ]
        self.add_input(
            f"{resource_name}_in",
            val=0.0,
            shape_by_conn=True,
            copy_shape=f"{resource_name}_out",
            units=resource_units,
            desc=f"{resource_name} input timeseries from production to storage",
        )

        self.add_output(
            f"{resource_name}_out",
            val=0.0,
            copy_shape=f"{resource_name}_in",
            units=resource_units,
            desc=f"{resource_name} output timeseries from plant after storage",
        )

    def compute(self, inputs, outputs):
        """
        Computation for the OM component.

        For a template class this is not implemented and raises an error.
        """

        raise NotImplementedError("This method should be implemented in a subclass.")


class PassThroughOpenLoopController(OpenLoopControllerBaseClass):
    def compute(self, inputs, outputs):
        "Pass through input to output flows"

        resource_name = self.options["tech_config"]["model_inputs"]["shared_parameters"][
            "resource_name"
        ]

        outputs[f"{resource_name}_out"] = inputs[f"{resource_name}_in"]

    def setup_partials(self):
        """
        Declare partial derivatives as unity throughout the design space.
        """
        resource_name = self.options["tech_config"]["model_inputs"]["shared_parameters"][
            "resource_name"
        ]

        # Declare partials for output with respect to input
        self.declare_partials(
            of=f"{resource_name}_out",
            wrt=f"{resource_name}_in",
            val=1.0,  # Unity partials for pass-through
        )
