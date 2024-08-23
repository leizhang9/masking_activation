-- masked dot product
-- pipeline latency: adds (ceil(ld(2*in_dim_g)) + 1 + 3) additional clock cycles

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
library work;
use work.dot_product_pkg.all;
use work.add_tree_pkg.all;
--use work.mask_util_pkg.all;
use work.prim_ops_pkg.all;

entity dot_product is
	generic (
		L_g           : positive := 32; -- fixed point width
		D_g           : positive := 2; -- number of shares
		in_dim_g      : positive := 6;
		pipelined_g   : boolean  := true
	);
	port (
		rnd_i      : in  std_ulogic_vector(L_g * (D_g - 1) - 1 downto 0);
		clk_i      : in  std_ulogic;
		rst_i      : in  std_ulogic;
		en_i       : in  std_ulogic;
		a_i        : in  std_ulogic_vector (L_g * D_g * in_dim_g - 1 downto 0);
		b_i        : in  std_ulogic_vector (L_g * D_g * in_dim_g - 1 downto 0);
		c_o        : out std_ulogic_vector (L_g * D_g - 1 downto 0)
	);
end dot_product;


architecture masking_arch of dot_product is
	
	component mod_adder is
		generic (
			L_g : positive
		);
		port (
			a_i : in  std_ulogic_vector (L_g - 1 downto 0);
			b_i : in  std_ulogic_vector (L_g - 1 downto 0);
			s_o : out std_ulogic_vector (L_g - 1 downto 0)
		);
	end component;

	component mod_multiplier_32 is
		port (
			a_i   : in  std_ulogic_vector (31 downto 0);
			b_i   : in  std_ulogic_vector (31 downto 0);
			p_o   : out std_ulogic_vector (31 downto 0);
			clk_i : in  std_ulogic;
			rst_i : in  std_ulogic
		);
	end component;

	component add_tree is
		generic (
			num_inputs_g   : positive;
			data_width_g   : positive;
			pipelined_g    : boolean := false
		);
		port (
			clk_i    : in  std_ulogic;
			rst_i    : in  std_ulogic;
			en_i     : in  std_ulogic;
			input_i  : in  std_ulogic_vector(num_inputs_g*data_width_g-1 downto 0);
			output_o : out std_ulogic_vector(data_width_g-1 downto 0)
		);
	end component;

	attribute DONT_TOUCH : string;
	attribute keep : string;
	
	signal c_s            : std_ulogic_vector (L_g * D_g - 1 downto 0);
	signal r_s            : std_ulogic_vector (L_g * (D_g - 1) - 1 downto 0);
	signal r_n_s          : std_ulogic_vector (L_g * (D_g - 1) - 1 downto 0);

	signal a_temp0_mult_s   : std_ulogic_vector (L_g * in_dim_g - 1 downto 0);
	signal b_temp0_mult_s   : std_ulogic_vector (L_g * in_dim_g - 1 downto 0);

	signal a_temp0_add_s  : std_ulogic_vector (L_g * in_dim_g - 1 downto 0);
	signal b_temp0_add_s  : std_ulogic_vector (L_g * in_dim_g - 1 downto 0);

	signal a_temp1_mult_s   : std_ulogic_vector (L_g * in_dim_g - 1 downto 0);
	signal b_temp1_mult_s   : std_ulogic_vector (L_g * in_dim_g - 1 downto 0);

	signal a_temp1_add_s  : std_ulogic_vector (L_g * in_dim_g - 1 downto 0);
	signal b_temp1_add_s  : std_ulogic_vector (L_g * in_dim_g - 1 downto 0);

	signal r_0_reg            : std_ulogic_vector (L_g * (D_g - 1) - 1 downto 0);
	signal r_n_0_reg          : std_ulogic_vector (L_g * (D_g - 1) - 1 downto 0);
	signal r_1_reg            : std_ulogic_vector (L_g * (D_g - 1) - 1 downto 0);
	signal r_n_1_reg          : std_ulogic_vector (L_g * (D_g - 1) - 1 downto 0);
	signal r_2_reg            : std_ulogic_vector (L_g * (D_g - 1) - 1 downto 0);
	signal r_n_2_reg          : std_ulogic_vector (L_g * (D_g - 1) - 1 downto 0);

	attribute keep of c_s            : signal is "true";
	attribute keep of r_s            : signal is "true";
	attribute keep of r_n_s          : signal is "true";
	attribute keep of a_temp0_mult_s : signal is "true";
	attribute keep of b_temp0_mult_s : signal is "true";
	attribute keep of a_temp0_add_s  : signal is "true";
	attribute keep of b_temp0_add_s  : signal is "true";
	attribute keep of a_temp1_mult_s : signal is "true";
	attribute keep of b_temp1_mult_s : signal is "true";
	attribute keep of a_temp1_add_s  : signal is "true";
	attribute keep of b_temp1_add_s  : signal is "true";

begin 

	r_s <= rnd_i;

	random_share_gen : for i in 0 to (D_g - 1) - 1 generate
		r_n_s(L_g * (i + 1) - 1 downto L_g * i) <= std_ulogic_vector(not(unsigned(rnd_i(L_g * (i + 1) - 1 downto L_g * i))) + 1);
	end generate;

	process(clk_i)
	begin
		if (rising_edge(clk_i)) then
			if (rst_i = '1') then
				r_0_reg     <= (others => '0');
				r_1_reg     <= (others => '0');
				r_2_reg     <= (others => '0');
				r_n_0_reg   <= (others => '0');
				r_n_1_reg   <= (others => '0');
				r_n_2_reg   <= (others => '0');
			else
				r_0_reg     <= r_s;
				r_1_reg     <= r_0_reg;
				r_2_reg     <= r_1_reg;
				r_n_0_reg   <= r_n_s;
				r_n_1_reg   <= r_n_0_reg;
				r_n_2_reg   <= r_n_1_reg;
			end if;
		end if;
	end process;

	c_o <= c_s;

	-- partial products for c(0) temp a
	mult0_0_gen : for i in 0 to in_dim_g - 1 generate

		mod_mult : mod_multiplier_32 
		port map (
			a_i => a_i(L_g * (D_g * i + 1) - 1 downto L_g * (D_g * i)), -- a_i(i)(0)
			b_i => b_i(L_g * (D_g * i + 2) - 1 downto L_g * (D_g * i + 1)), -- b_i(i)(1)
			p_o => a_temp0_mult_s((i+1)*L_g - 1 downto i*L_g),
			clk_i    => clk_i,
			rst_i    => rst_i
		);

	end generate;
	
	-- add random number to partial products for c(0) of temp a
	add0_0_gen : for i in 0 to in_dim_g - 1 generate

		add_tree_inst : add_tree generic map (
			num_inputs_g => 2,
			data_width_g => L_g,
			pipelined_g  => pipelined_g
		) port map (
			clk_i    => clk_i,
			rst_i    => rst_i,
			en_i     => en_i,
			input_i  => r_2_reg & a_temp0_mult_s((i+1)*L_g - 1 downto i*L_g),
			output_o => a_temp0_add_s((i+1)*L_g - 1 downto i*L_g)
		);

	end generate;

	-- partial products for c(0) temp b
	mult0_1_gen : for i in 0 to in_dim_g - 1 generate
		
		mod_mult : mod_multiplier_32 
		port map (
			a_i => a_i(L_g * (D_g * i + 2) - 1 downto L_g * (D_g * i + 1)), -- a_i(i)(1)
			b_i => b_i(L_g * (D_g * i + 1) - 1 downto L_g * (D_g * i)), -- b_i(i)(0)
			p_o => b_temp0_mult_s((i+1)*L_g - 1 downto i*L_g),
			clk_i    => clk_i,
			rst_i    => rst_i
		);
		
	end generate;
	
	-- add random number to partial products for c(0) of temp b
	add0_1_gen : for i in 0 to in_dim_g - 1 generate

		add_tree_inst : add_tree generic map (
			num_inputs_g => 2,
			data_width_g => L_g,
			pipelined_g  => pipelined_g
		) port map (
			clk_i    => clk_i,
			rst_i    => rst_i,
			en_i     => en_i,
			input_i  => r_2_reg & b_temp0_mult_s((i+1)*L_g - 1 downto i*L_g),
			output_o => b_temp0_add_s((i+1)*L_g - 1 downto i*L_g)
		);

	end generate;
	
	-- adder tree for c(0)
	add_tree_c0 : add_tree generic map (
		num_inputs_g => (2*in_dim_g),
		data_width_g => L_g,
		pipelined_g  => pipelined_g
	) port map (
		clk_i    => clk_i,
		rst_i    => rst_i,
		en_i     => en_i,
		input_i  => a_temp0_add_s & b_temp0_add_s,
		output_o => c_s(L_g - 1 downto 0)
	);
	
	-- partial products for c(1) temp a
	mult1_0_gen : for i in 0 to in_dim_g - 1 generate
		
		mod_mult : mod_multiplier_32 
		port map (
			a_i => a_i(L_g * (D_g * i + 1) - 1 downto L_g * (D_g * i)), -- a_i(i)(0)
			b_i => b_i(L_g * (D_g * i + 1) - 1 downto L_g * (D_g * i)), -- b_i(i)(0)
			p_o => a_temp1_mult_s((i+1)*L_g - 1 downto i*L_g),
			clk_i    => clk_i,
			rst_i    => rst_i
		);
		
	end generate;
	
	-- add random number to partial products for c(1) of temp a
	add1_0_gen : for i in 0 to in_dim_g - 1 generate
	
		add_tree_inst : add_tree generic map (
			num_inputs_g => 2,
			data_width_g => L_g,
			pipelined_g  => pipelined_g
		) port map (
			clk_i    => clk_i,
			rst_i    => rst_i,
			en_i     => en_i,
			input_i  => r_n_2_reg & a_temp1_mult_s((i+1)*L_g - 1 downto i*L_g),
			output_o => a_temp1_add_s((i+1)*L_g - 1 downto i*L_g)
		);

	end generate;
	
	-- partial products for c(1) temp b
	mult1_1_gen : for i in 0 to in_dim_g - 1 generate
		
		mod_mult : mod_multiplier_32 
		port map (
			a_i => a_i(L_g * (D_g * i + 2) - 1 downto L_g * (D_g * i + 1)), -- a_i(i)(1)
			b_i => b_i(L_g * (D_g * i + 2) - 1 downto L_g * (D_g * i + 1)), -- b_i(i)(1)
			p_o => b_temp1_mult_s((i+1)*L_g - 1 downto i*L_g),
			clk_i    => clk_i,
			rst_i    => rst_i
		);

	end generate;
	
	-- add random number to partial products for c(1) of temp b
	add1_1_gen : for i in 0 to in_dim_g - 1 generate
	
		add_tree_inst : add_tree generic map (
			num_inputs_g => 2,
			data_width_g => L_g,
			pipelined_g  => pipelined_g
		) port map (
			clk_i    => clk_i,
			rst_i    => rst_i,
			en_i     => en_i,
			input_i  => r_n_2_reg & b_temp1_mult_s((i+1)*L_g - 1 downto i*L_g),
			output_o => b_temp1_add_s((i+1)*L_g - 1 downto i*L_g)
		);

	end generate;
	
	-- adder tree for c(0)
	add_tree_c1 : add_tree generic map (
		num_inputs_g => (2*in_dim_g),
		data_width_g => L_g,
		pipelined_g  => pipelined_g
	) port map (
		clk_i    => clk_i,
		rst_i    => rst_i,
		en_i     => en_i,
		input_i  => a_temp1_add_s & b_temp1_add_s,
		output_o => c_s(L_g * 2 - 1 downto L_g)
	);

end masking_arch;

