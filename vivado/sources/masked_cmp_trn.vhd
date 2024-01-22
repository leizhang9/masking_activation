library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use work.conversion_pkg.all;
use work.masked_add_pkg.all;

entity masked_cmp_trn is
	generic (
		L_g            				: positive := 16; -- fixed point width
		D_g            				: positive := 2; -- number of shares
		fp_fractional_bits_g 	: positive := 3
	);
	port (
		clk_i          : in  std_ulogic;
		rst_i          : in  std_ulogic;
		a_i            : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
		b_i            : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
		rnd_i          : in  std_ulogic_vector (18 * L_g * (D_g - 1) - 1 downto 0);
    start_i        : in  std_logic;
		done_o				 : out std_ulogic;
		c_o            : out std_ulogic_vector (L_g * D_g - 1 downto 0);
		d_o            : out std_ulogic_vector (L_g * D_g - 1 downto 0);
		trn_o          : out std_ulogic_vector (L_g * D_g - 1 downto 0)
	);
end;

architecture behavioral of masked_cmp_trn is

	signal t_s 									: std_ulogic_vector(L_g * D_g - 1 downto 0);
	signal t_reg 								: std_ulogic_vector(L_g * D_g - 1 downto 0);
	signal rnd_sub_s						: std_ulogic_vector(L_g * D_g - 1 downto 0);
	signal rnd_sub_reg0					: std_ulogic_vector(L_g * D_g - 1 downto 0);

	signal a_reg0								: std_ulogic_vector(L_g * D_g - 1 downto 0);
	signal b_reg0								: std_ulogic_vector(L_g * D_g - 1 downto 0);

	signal boolean_shares_s   	: std_logic_vector(L_g * D_g - 1 downto 0);
	signal boolean_shares_reg0 	: std_ulogic_vector(L_g * D_g - 1 downto 0);
	signal boolean_shares_reg1 	: std_ulogic_vector(L_g * D_g - 1 downto 0);
	signal boolean_shares_n_s 	: std_logic_vector(L_g * D_g - 1 downto 0);
	signal boolean_shares_regn	: std_ulogic_vector(L_g * D_g - 1 downto 0);

	signal rnd_a2b_s        		: std_ulogic_vector(5 * L_g * (D_g - 1) - 1 downto 0);
	signal rnd_a2b_reg0      		: std_ulogic_vector(5 * L_g * (D_g - 1) - 1 downto 0);
  signal done_a2b 						: std_logic;

	signal rnd_b2a_c_s        	: std_ulogic_vector(11 * L_g * (D_g - 1) - 1 downto 0);
	signal rnd_b2a_c_reg0      	: std_ulogic_vector(11 * L_g * (D_g - 1) - 1 downto 0);
  signal done_b2a_c 					: std_logic;
	signal start_b2a_c_s				: std_logic;
	signal start_b2a_c_reg0			: std_logic;
	signal start_b2a_c_reg1			: std_logic;
	signal start_b2a_c_reg2			: std_logic;
	signal b2a_c_i_s						: std_logic_vector(L_g * D_g - 1 downto 0);
	signal b2a_c_i_reg0					: std_logic_vector(L_g * D_g - 1 downto 0);

	signal msb_shares_s					: std_ulogic_vector(D_g - 1 downto 0);
	signal msb_shares_reg0			: std_ulogic_vector(D_g - 1 downto 0);
	signal msb_dummy_s					: std_ulogic_vector(L_g * D_g - 1 - 2 downto 0);
	signal msb_dummy_reg0				: std_ulogic_vector(L_g * D_g - 1 - 2 downto 0);

	signal trunc_share_0_s	    : std_ulogic_vector(L_g - 1 downto 0);
	signal trunc_share_1_s  	  : std_ulogic_vector(L_g - 1 downto 0);
	signal trunc_share_0_reg0   : std_ulogic_vector(L_g - 1 downto 0);
	signal trunc_share_1_reg0   : std_ulogic_vector(L_g - 1 downto 0);
	signal trunc_share_0_n_s    : std_ulogic_vector(L_g - 1 downto 0);
	signal trunc_share_1_n_s 	  : std_ulogic_vector(L_g - 1 downto 0);
	signal trunc_share_0_regn   : std_ulogic_vector(L_g - 1 downto 0);
	signal trunc_share_1_regn   : std_ulogic_vector(L_g - 1 downto 0);

	signal start_reg0						: std_logic;
	signal start_reg1						: std_logic;
	signal start_reg2						: std_logic;
	signal start_reg3						: std_logic;
	signal start_reg4						: std_logic;

	signal c_s_0								: std_logic_vector(L_g * (D_g - 1) - 1 downto 0);
	signal c_s_1								: std_logic_vector(L_g * (D_g - 1) - 1 downto 0);
	signal c_reg 								: std_ulogic_vector(L_g * D_g - 1 downto 0);

	signal msb_shares_n_s				: std_ulogic_vector(D_g - 1 downto 0);
	signal msb_shares_n_reg0		: std_ulogic_vector(D_g - 1 downto 0);
	signal msb_dummy_n_s				: std_ulogic_vector(L_g * D_g - 1 - 2 downto 0);
	signal msb_dummy_n_reg0			: std_ulogic_vector(L_g * D_g - 1 - 2 downto 0);

	signal b2a_d_i_s						: std_logic_vector(L_g * D_g - 1 downto 0);
	signal b2a_d_i_reg0					: std_logic_vector(L_g * D_g - 1 downto 0);
	signal rnd_b2a_d_s        	: std_ulogic_vector(11 * L_g * (D_g - 1) - 1 downto 0);
	signal rnd_b2a_d_reg0				: std_ulogic_vector(11 * L_g * (D_g - 1) - 1 downto 0);
	signal done_b2a_d						: std_logic;
	signal start_b2a_d_reg0			: std_logic;

	signal done_b2a_t						: std_logic;
	signal start_b2a_t_reg0			: std_logic;
	signal rnd_b2a_t_s        	: std_ulogic_vector(11 * L_g * (D_g - 1) - 1 downto 0);
	signal rnd_b2a_t_reg0				: std_ulogic_vector(11 * L_g * (D_g - 1) - 1 downto 0);
	signal b2a_t_i_s						: std_logic_vector(L_g * D_g - 1 downto 0);
	signal b2a_t_i_reg0					: std_logic_vector(L_g * D_g - 1 downto 0);

	signal trn_s_0							: std_logic_vector(L_g * (D_g - 1) - 1 downto 0);
	signal trn_s_1							: std_logic_vector(L_g * (D_g - 1) - 1 downto 0);
	signal trn_reg 							: std_ulogic_vector(L_g * D_g - 1 downto 0);

	signal d_s_0								: std_logic_vector(L_g * (D_g - 1) - 1 downto 0);
	signal d_s_1								: std_logic_vector(L_g * (D_g - 1) - 1 downto 0);
	signal d_reg 								: std_ulogic_vector(L_g * D_g - 1 downto 0);

	signal done_reg 						: std_ulogic;
	signal done_reg1 						: std_ulogic;

	signal rst_a2b							: std_logic;
	signal rst_b2a							: std_logic;

	attribute DONT_TOUCH : string;
  attribute DONT_TOUCH of masked_sub_inst 	: label is "true";
	attribute DONT_TOUCH of conv_a2b_inst 		: label is "true";
	attribute DONT_TOUCH of conv_b2a_inst0 		: label is "true";
	attribute DONT_TOUCH of conv_b2a_inst1 		: label is "true";
	attribute DONT_TOUCH of conv_b2a_inst2 		: label is "true";

	attribute keep : string;
	attribute keep of t_s                			: signal is "true";
	attribute keep of t_reg              			: signal is "true";
	attribute keep of boolean_shares_s   			: signal is "true";
	attribute keep of boolean_shares_reg0     : signal is "true";
	attribute keep of boolean_shares_reg1     : signal is "true";
	attribute keep of boolean_shares_regn     : signal is "true";
  attribute keep of rnd_a2b_s          			: signal is "true";
	attribute keep of rnd_a2b_reg0       			: signal is "true";
	attribute keep of msb_shares_s	    			: signal is "true";
	attribute keep of msb_shares_reg0    			: signal is "true";
	attribute keep of msb_dummy_s		    			: signal is "true";
	attribute keep of msb_dummy_reg0    			: signal is "true";
  attribute keep of rnd_sub_s          			: signal is "true";
	attribute keep of rnd_sub_reg0       			: signal is "true";
	attribute keep of trunc_share_0_s   			: signal is "true";
	attribute keep of trunc_share_1_s   			: signal is "true";
	attribute keep of trunc_share_0_reg0 			: signal is "true";
	attribute keep of trunc_share_1_reg0			: signal is "true";
	attribute keep of rnd_b2a_c_s        			: signal is "true";
	attribute keep of rnd_b2a_c_reg0     			: signal is "true";
	attribute keep of c_s_0              			: signal is "true";
	attribute keep of c_s_1              			: signal is "true";
	attribute keep of c_reg              			: signal is "true";
	attribute keep of b2a_c_i_s          			: signal is "true";
	attribute keep of b2a_c_i_reg0       			: signal is "true";
	attribute keep of trunc_share_0_n_s       : signal is "true";
	attribute keep of trunc_share_1_n_s     	: signal is "true";
	attribute keep of trunc_share_0_regn    	: signal is "true";
	attribute keep of trunc_share_1_regn      : signal is "true";
	attribute keep of msb_shares_n_s     	  	: signal is "true";
	attribute keep of msb_shares_n_reg0 	    : signal is "true";
	attribute keep of msb_dummy_n_s    				: signal is "true";
	attribute keep of msb_dummy_n_reg0    	  : signal is "true";
	attribute keep of b2a_d_i_s          			: signal is "true";
	attribute keep of b2a_d_i_reg0       			: signal is "true";
	attribute keep of rnd_b2a_d_reg0     			: signal is "true";
	attribute keep of done_b2a_d		     			: signal is "true";
	attribute keep of d_s_0              			: signal is "true";
	attribute keep of d_s_1              			: signal is "true";
	attribute keep of d_reg              			: signal is "true";
	attribute keep of b2a_t_i_s        				: signal is "true";
	attribute keep of b2a_t_i_reg0     				: signal is "true";
	attribute keep of rnd_b2a_t_s		     			: signal is "true";
	attribute keep of rnd_b2a_d_s		     			: signal is "true";
	attribute keep of rnd_b2a_t_reg0     			: signal is "true";
	attribute keep of boolean_shares_n_s 			: signal is "true";
	attribute keep of trn_s_1 			    			: signal is "true";
	attribute keep of trn_s_0					 				: signal is "true";
	attribute keep of trn_reg									: signal is "true";
	attribute keep of rst_a2b									: signal is "true";
	attribute keep of rst_b2a									: signal is "true";

	signal u_noise0 : std_logic_vector(15 downto 0);
	signal u_noise1 : std_logic_vector(15 downto 0);

begin

	-- signal assignments
	rnd_a2b_s   				<= rnd_i(5 * L_g * (D_g - 1) - 1 downto 0);
	rnd_sub_s						<= rnd_i(7 * L_g * (D_g - 1) - 1 downto 5 * L_g * (D_g - 1));
	rnd_b2a_c_s					<= rnd_i(18 * L_g * (D_g - 1) - 1 downto 7 * L_g * (D_g - 1));
	--rnd_b2a_d_s					<= std_ulogic_vector(rotate_right(unsigned(rnd_i(18 * L_g * (D_g - 1) - 1 downto 7 * L_g * (D_g - 1))), 5 * L_g));
	--rnd_b2a_t_s					<= std_ulogic_vector(rotate_left(unsigned(rnd_i(18 * L_g * (D_g - 1) - 1 downto 7 * L_g * (D_g - 1))), 5 * L_g));
	start_b2a_c_s 			<= done_a2b;
	b2a_c_i_s 				 	<= std_logic_vector(rnd_b2a_c_reg0(11 * L_g - 2 downto 10 * L_g)) & std_logic(msb_shares_reg0(0)) & std_logic_vector(rnd_b2a_c_reg0(11 * L_g - 2 downto 10 * L_g)) & std_logic(msb_shares_reg0(1));
	boolean_shares_n_s 	<= not boolean_shares_reg0;
	b2a_d_i_s						<= std_logic_vector(rnd_b2a_d_reg0(11 * L_g - 2 downto 10 * L_g)) & std_logic(msb_shares_reg0(0)) & std_logic_vector(rnd_b2a_d_reg0(11 * L_g - 2 downto 10 * L_g)) & std_logic(msb_shares_n_reg0(1)) xor (u_noise0 & u_noise1 & u_noise0 & u_noise1);
	b2a_t_i_s						<= (std_logic_vector(rnd_b2a_d_reg0(11 * L_g - 1 downto 10 * L_g)) xor std_logic_vector(trunc_share_0_reg0)) & (std_logic_vector(rnd_b2a_d_reg0(11 * L_g - 1 downto 10 * L_g)) xor std_logic_vector(trunc_share_1_reg0)) xor (u_noise1 & u_noise0 & u_noise1 & u_noise0);
	c_o 								<= c_reg;
  d_o 								<= d_reg;
  trn_o 							<= trn_reg;
	done_o							<= done_reg;

	shift_logic : process(rnd_i)
		variable tab0 : std_logic_vector(L_g - 1 downto 0);
		variable tab1 : std_logic_vector(L_g - 1 downto 0);
	begin
		tab0 := rnd_i(7 * L_g * (D_g - 1) - 1 downto 6 * L_g * (D_g - 1));
		tab1 := rnd_i(6 * L_g * (D_g - 1) - 1 downto 5 * L_g * (D_g - 1));
		shift_loop : for i in 8 to 18 loop
			rnd_b2a_d_s((i - 7) * L_g * (D_g - 1) - 1 downto (i - 8) * L_g * (D_g - 1)) <= rnd_i(i * L_g * (D_g - 1) - 1 downto (i - 1) * L_g * (D_g - 1)) xor tab0;
			rnd_b2a_t_s((i - 7) * L_g * (D_g - 1) - 1 downto (i - 8) * L_g * (D_g - 1)) <= rnd_i(i * L_g * (D_g - 1) - 1 downto (i - 1) * L_g * (D_g - 1)) xor tab1;
		end loop;
	end process;

	lfsr0 : entity work.noise_gen(arch)
	port map (
		clk => clk_i,
		n_reset => not rst_i,
		enable => '1',
		g_noise_out => open,
		u_noise_out => u_noise0
	);

	lfsr1 : entity work.noise_gen(arch)
	generic map (
		seed0 => 58742,
		seed1 => 25421
	)
	port map (
		clk => clk_i,
		n_reset => not rst_i,
		enable => '1',
		g_noise_out => open,
		u_noise_out => u_noise1
	);

	-- truncation
	-- share 0
	trunc_share_0_s 	<= std_ulogic_vector(shift_right(signed(boolean_shares_reg1(L_g * D_g - 1 downto L_g)), fp_fractional_bits_g));
	trunc_share_0_n_s	<= std_ulogic_vector(shift_right(signed(boolean_shares_regn(L_g * D_g - 1 downto L_g)), fp_fractional_bits_g));
	-- share 1
	trunc_share_1_s 	<= std_ulogic_vector(shift_right(signed(boolean_shares_reg1(L_g - 1 downto 0)), fp_fractional_bits_g));
	trunc_share_1_n_s <= std_ulogic_vector(shift_right(signed(boolean_shares_regn(L_g - 1 downto 0)), fp_fractional_bits_g));


	msb_share_gen : for i in 0 to D_g - 1 generate
		msb_shares_s(i) 																					<= boolean_shares_reg0(L_g * (i + 1) - 1);
		msb_dummy_s(L_g * (i + 1) - 2 - i downto (L_g - 1) * i) 	<= boolean_shares_reg0(L_g * (i + 1) - 2 downto L_g * i);
		msb_shares_n_s(i) 																				<= boolean_shares_regn(L_g * (i + 1) - 1);
		msb_dummy_n_s(L_g * (i + 1) - 2 - i downto (L_g - 1) * i) <= boolean_shares_regn(L_g * (i + 1) - 2 downto L_g * i);
	end generate;

	rst_proc : process(clk_i)
	begin
		if clk_i'event and clk_i = '1' then
			if rst_i = '1' then
				rst_a2b <= '1';
				rst_b2a <= '1';
			end if;
			if start_reg0 = '1' then
				rst_a2b <= '0';
			elsif start_b2a_c_reg0 = '1' then
				rst_a2b <= '0'; --'1';
			end if;
			if start_b2a_c_reg0 = '1' then
				rst_b2a <= '0';
			elsif done_reg = '1' then
				rst_b2a <= '0'; --'1';
			end if;
		end if;
	end process;

	reg : process(clk_i) is
	begin
		if clk_i'event and clk_i = '1' then
			if (rst_i = '1') then
				rnd_a2b_reg0        <= (others => '0');
				t_reg               <= (others => '0');
				boolean_shares_reg0 <= (others => '0');
				start_reg0 					<= '0';
				start_reg1 					<= '0';
				start_reg2 					<= '0';
				start_reg3 					<= '0';
				start_reg4 					<= '0';
				msb_shares_reg0			<= (others => '0');
				msb_dummy_reg0			<= (others => '0');
				rnd_sub_reg0				<= (others => '0');
				boolean_shares_reg1 <= (others => '0');
				trunc_share_0_reg0	<= (others => '0');
				trunc_share_1_reg0	<= (others => '0');
				rnd_b2a_c_reg0			<= (others => '0');
				c_reg								<= (others => '0');
				start_b2a_c_reg0		<= '0';
				start_b2a_c_reg1		<= '0';
				start_b2a_c_reg2		<= '0';
				a_reg0							<= (others => '0');
				b_reg0							<= (others => '0');
				b2a_c_i_reg0				<= (others => '0');
				boolean_shares_regn <= (others => '0');
				trunc_share_0_regn	<= (others => '0');
				trunc_share_1_regn	<= (others => '0');
				msb_shares_n_reg0		<= (others => '0');
				msb_dummy_n_reg0		<= (others => '0');
				rnd_b2a_d_reg0			<= (others => '0');
				b2a_d_i_reg0				<= (others => '0');
				d_reg								<= (others => '0');
				start_b2a_d_reg0		<= '0';
				start_b2a_t_reg0		<= '0';
				trn_reg							<= (others => '0');
				done_reg 						<= '0';
				b2a_t_i_reg0				<= (others => '0');
			else
				if start_b2a_c_reg0 = '1' then
					rnd_b2a_c_reg0			<= rnd_b2a_c_s;
					msb_shares_reg0			<= msb_shares_s;
					msb_dummy_reg0			<= msb_dummy_s;
				end if;
				if start_b2a_c_reg1 = '1' then
					rnd_b2a_d_reg0 			<= rnd_b2a_d_s;

					msb_shares_n_reg0		<= msb_shares_n_s;
					msb_dummy_n_reg0		<= msb_dummy_n_s;
					rnd_b2a_t_reg0			<= rnd_b2a_t_s;

					trunc_share_0_reg0	<= trunc_share_0_s;
					trunc_share_1_reg0	<= trunc_share_1_s;
					trunc_share_0_regn	<= trunc_share_0_n_s;
					trunc_share_1_regn	<= trunc_share_1_n_s;
				end if;
				b2a_c_i_reg0 				<= b2a_c_i_s;
				b2a_t_i_reg0				<= b2a_t_i_s;
				b2a_d_i_reg0				<= b2a_d_i_s;
				boolean_shares_reg0 <= std_ulogic_vector(boolean_shares_s);
				rnd_a2b_reg0        <= rnd_a2b_s;
				t_reg               <= t_s;
				boolean_shares_reg1 <= boolean_shares_reg0;
				start_reg0					<= start_i;
				start_reg1					<= start_reg0;
				start_reg2					<= start_reg1;
				start_reg3					<= start_reg2;
				start_reg4					<= start_reg3;
				msb_dummy_reg0			<= msb_dummy_s;
				rnd_sub_reg0				<= rnd_sub_s;
				if done_b2a_c = '1' then
					c_reg								<= std_ulogic_vector(c_s_0) & std_ulogic_vector(c_s_1);
				end if;
				start_b2a_c_reg0		<= start_b2a_c_s;
				start_b2a_c_reg1		<= start_b2a_c_reg0;
				start_b2a_c_reg2		<= start_b2a_c_reg1;
				a_reg0							<= a_i;
				b_reg0							<= b_i;
				boolean_shares_regn	<= boolean_shares_n_s;
				if done_b2a_d = '1' then
						d_reg								<= std_ulogic_vector(d_s_0) & std_ulogic_vector(d_s_1);
				end if;
				start_b2a_d_reg0		<= start_b2a_c_reg2;
				start_b2a_t_reg0		<= start_b2a_c_reg2;
				if done_b2a_t = '1' then
					trn_reg							<= std_ulogic_vector(trn_s_0) & std_ulogic_vector(trn_s_1);
				end if;
				done_reg 						<= done_b2a_t;
				done_reg1						<= done_reg;
			end if;
		end if;
	end process reg;

	masked_sub_inst : masked_add generic map (
		L_g      => L_g,
		D_g      => D_g,
		sni_g    => false,
		sub_g    => true
	) port map (
	  clk_i	 	 => clk_i,
		rst_i	 	 => rst_i,
		a_i      => a_reg0,
		b_i      => b_reg0,
		rnd_i    => rnd_sub_reg0,
		c_o      => t_s
	);

  conv_a2b_inst : entity work.convert_a_to_b
  port map (
    clk => std_logic(clk_i),
    rst => std_logic(rst_i) or rst_a2b,
    start => start_reg4,
    A0 => std_logic_vector(t_reg(L_g * D_g - 1 downto L_g)),
    A1 => std_logic_vector(t_reg(L_g - 1 downto 0)),
    r0 => std_logic_vector(rnd_a2b_reg0(L_g - 1 downto 0)),
    r1 => std_logic_vector(rnd_a2b_reg0(2 * L_g - 1 downto L_g)),
    r2 => std_logic_vector(rnd_a2b_reg0(3 * L_g - 1 - 1 downto 2 * L_g)),
    r3 => std_logic_vector(rnd_a2b_reg0(4 * L_g - 1 - 1 downto 3 * L_g)),
    r4 => std_logic_vector(rnd_a2b_reg0(5 * L_g - 1 - 1 downto 4 * L_g)),
    done => done_a2b,
    z0 => boolean_shares_s(L_g - 1 downto 0),
    z1 => boolean_shares_s(L_g * D_g - 1 downto L_g)
  );

	conv_b2a_inst0 : entity work.convert_b_to_a
	port map (
		clk 	=> std_logic(clk_i),
		rst   => std_logic(rst_i) or rst_b2a,
		start => start_b2a_c_reg2,
		x0    => b2a_c_i_reg0(L_g * D_g - 1 downto L_g),
		x1    => b2a_c_i_reg0(L_g - 1 downto 0),
		r0    => std_logic_vector(rnd_b2a_c_reg0(L_g - 1 downto 0)),
		c_r0  => std_logic_vector(rnd_b2a_c_reg0(2 * L_g - 1 downto L_g)),
		c_r1  => std_logic_vector(rnd_b2a_c_reg0(3 * L_g - 1 downto 2 * L_g)),
		c_r2  => std_logic_vector(rnd_b2a_c_reg0(4 * L_g - 1 - 1 downto 3 * L_g)),
		c_r3  => std_logic_vector(rnd_b2a_c_reg0(5 * L_g - 1 - 1 downto 4 * L_g)),
		c_r4  => std_logic_vector(rnd_b2a_c_reg0(6 * L_g - 1 - 1 downto 5 * L_g)),
		a_r0  => std_logic_vector(rnd_b2a_c_reg0(7 * L_g - 1 - 1 downto 6 * L_g)),
		a_r1  => std_logic_vector(rnd_b2a_c_reg0(8 * L_g - 1 - 1 downto 7 * L_g)),
		a_r2  => std_logic_vector(rnd_b2a_c_reg0(9 * L_g - 1 - 1 downto 8 * L_g)),
		x_r   => std_logic_vector(rnd_b2a_c_reg0(10 * L_g - 1 downto 9 * L_g)),
		done  => done_b2a_d,
		A0    => d_s_0,
		A1    => d_s_1
	);

	conv_b2a_inst1 : entity work.convert_b_to_a
	port map (
		clk 	=> std_logic(clk_i),
		rst   => std_logic(rst_i) or rst_b2a,
		start => start_b2a_d_reg0,
		x0    => b2a_d_i_reg0(L_g * D_g - 1 downto L_g),
		x1    => b2a_d_i_reg0(L_g - 1 downto 0),
		r0    => std_logic_vector(rnd_b2a_d_reg0(L_g - 1 downto 0)),
		c_r0  => std_logic_vector(rnd_b2a_d_reg0(2 * L_g - 1 downto L_g)),
		c_r1  => std_logic_vector(rnd_b2a_d_reg0(3 * L_g - 1 downto 2 * L_g)),
		c_r2  => std_logic_vector(rnd_b2a_d_reg0(4 * L_g - 1 - 1 downto 3 * L_g)),
		c_r3  => std_logic_vector(rnd_b2a_d_reg0(5 * L_g - 1 - 1 downto 4 * L_g)),
		c_r4  => std_logic_vector(rnd_b2a_d_reg0(6 * L_g - 1 - 1 downto 5 * L_g)),
		a_r0  => std_logic_vector(rnd_b2a_d_reg0(7 * L_g - 1 - 1 downto 6 * L_g)),
		a_r1  => std_logic_vector(rnd_b2a_d_reg0(8 * L_g - 1 - 1 downto 7 * L_g)),
		a_r2  => std_logic_vector(rnd_b2a_d_reg0(9 * L_g - 1 - 1 downto 8 * L_g)),
		x_r   => std_logic_vector(rnd_b2a_d_reg0(10 * L_g - 1 downto 9 * L_g)),
		done  => done_b2a_c,
		A0    => c_s_0,
		A1    => c_s_1
	);

	conv_b2a_inst2 : entity work.convert_b_to_a
	port map (
		clk 	=> std_logic(clk_i),
		rst   => std_logic(rst_i) or rst_b2a,
		start => start_b2a_t_reg0,
		x0    => b2a_t_i_reg0(L_g * D_g - 1 downto L_g),
		x1    => b2a_t_i_reg0(L_g - 1 downto 0),
		r0    => std_logic_vector(rnd_b2a_t_reg0(L_g - 1 downto 0)),
		c_r0  => std_logic_vector(rnd_b2a_t_reg0(2 * L_g - 1 downto L_g)),
		c_r1  => std_logic_vector(rnd_b2a_t_reg0(3 * L_g - 1 downto 2 * L_g)),
		c_r2  => std_logic_vector(rnd_b2a_t_reg0(4 * L_g - 1 - 1 downto 3 * L_g)),
		c_r3  => std_logic_vector(rnd_b2a_t_reg0(5 * L_g - 1 - 1 downto 4 * L_g)),
		c_r4  => std_logic_vector(rnd_b2a_t_reg0(6 * L_g - 1 - 1 downto 5 * L_g)),
		a_r0  => std_logic_vector(rnd_b2a_t_reg0(7 * L_g - 1 - 1 downto 6 * L_g)),
		a_r1  => std_logic_vector(rnd_b2a_t_reg0(8 * L_g - 1 - 1 downto 7 * L_g)),
		a_r2  => std_logic_vector(rnd_b2a_t_reg0(9 * L_g - 1 - 1 downto 8 * L_g)),
		x_r   => std_logic_vector(rnd_b2a_t_reg0(10 * L_g - 1 downto 9 * L_g)),
		done  => done_b2a_t,
		A0    => trn_s_0,
		A1    => trn_s_1
	);

end behavioral;
